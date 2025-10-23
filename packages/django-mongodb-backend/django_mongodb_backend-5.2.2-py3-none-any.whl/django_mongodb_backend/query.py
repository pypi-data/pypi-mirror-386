from functools import reduce, wraps
from operator import add as add_operator

from django.core.exceptions import EmptyResultSet, FullResultSet
from django.db import DatabaseError, IntegrityError, NotSupportedError
from django.db.models.expressions import Case, Col, When
from django.db.models.functions import Mod
from django.db.models.lookups import Exact
from django.db.models.sql.constants import INNER
from django.db.models.sql.datastructures import Join
from django.db.models.sql.where import AND, OR, XOR, ExtraWhere, NothingNode, WhereNode
from pymongo.errors import BulkWriteError, DuplicateKeyError, PyMongoError


def wrap_database_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except BulkWriteError as e:
            if "E11000 duplicate key error" in str(e):
                raise IntegrityError from e
            raise
        except DuplicateKeyError as e:
            raise IntegrityError from e
        except PyMongoError as e:
            raise DatabaseError from e

    return wrapper


class MongoQuery:
    """
    Compilers build a MongoQuery when they want to fetch some data. They work
    by first allowing sql.compiler.SQLCompiler to partly build a sql.Query,
    constructing a MongoQuery query on top of it, and then iterating over its
    results.

    This class provides a framework for converting the SQL constraint tree
    built by Django to a "representation" more suitable for MongoDB.
    """

    def __init__(self, compiler):
        self.compiler = compiler
        self.query = compiler.query
        self.ordering = []
        self.match_mql = {}
        self.subqueries = None
        self.lookup_pipeline = None
        self.project_fields = None
        self.aggregation_pipeline = compiler.aggregation_pipeline
        self.search_pipeline = compiler.search_pipeline
        self.extra_fields = None
        self.combinator_pipeline = None
        # $lookup stage that encapsulates the pipeline for performing a nested
        # subquery.
        self.subquery_lookup = None

    def __repr__(self):
        return f"<MongoQuery: {self.match_mql!r} ORDER {self.ordering!r}>"

    @wrap_database_errors
    def delete(self):
        """Execute a delete query."""
        if self.compiler.subqueries:
            raise NotSupportedError("Cannot use QuerySet.delete() when a subquery is required.")
        return self.compiler.collection.delete_many(
            self.match_mql, session=self.compiler.connection.session
        ).deleted_count

    @wrap_database_errors
    def get_cursor(self):
        """
        Return a pymongo CommandCursor that can be iterated on to give the
        results of the query.
        """
        return self.compiler.collection.aggregate(
            self.get_pipeline(), session=self.compiler.connection.session
        )

    def get_pipeline(self):
        pipeline = []
        if self.search_pipeline:
            pipeline.extend(self.search_pipeline)
        if self.lookup_pipeline:
            pipeline.extend(self.lookup_pipeline)
        for query in self.subqueries or ():
            pipeline.extend(query.get_pipeline())
        if self.match_mql:
            pipeline.append({"$match": self.match_mql})
        if self.aggregation_pipeline:
            pipeline.extend(self.aggregation_pipeline)
        if self.project_fields:
            pipeline.append({"$project": self.project_fields})
        if self.combinator_pipeline:
            pipeline.extend(self.combinator_pipeline)
        if self.extra_fields:
            pipeline.append({"$addFields": self.extra_fields})
        if self.ordering:
            pipeline.append({"$sort": self.ordering})
        if self.query.low_mark > 0:
            pipeline.append({"$skip": self.query.low_mark})
        if self.query.high_mark is not None:
            pipeline.append({"$limit": self.query.high_mark - self.query.low_mark})
        if self.subquery_lookup:
            table_output = self.subquery_lookup["as"]
            pipeline = [
                {"$lookup": {**self.subquery_lookup, "pipeline": pipeline}},
                {
                    "$set": {
                        table_output: {
                            "$cond": {
                                "if": {
                                    "$or": [
                                        {"$eq": [{"$type": f"${table_output}"}, "missing"]},
                                        {"$eq": [{"$size": f"${table_output}"}, 0]},
                                    ]
                                },
                                "then": {},
                                "else": {"$arrayElemAt": [f"${table_output}", 0]},
                            }
                        }
                    }
                },
            ]
        return pipeline


def extra_where(self, compiler, connection):  # noqa: ARG001
    raise NotSupportedError("QuerySet.extra() is not supported on MongoDB.")


def join(self, compiler, connection, pushed_filter_expression=None):
    """
    Generate a MongoDB $lookup stage for a join.

    `pushed_filter_expression` is a Where expression involving fields from the
    joined collection which can be pushed from the WHERE ($match) clause to the
    JOIN ($lookup) clause to improve performance.
    """
    parent_template = "parent__field__"

    def _get_reroot_replacements(expression):
        if not expression:
            return None
        columns = []
        for expr in expression.leaves():
            # Determine whether the column needs to be transformed or rerouted
            # as part of the subquery.
            for hand_side in ["lhs", "rhs"]:
                hand_side_value = getattr(expr, hand_side, None)
                if isinstance(hand_side_value, Col):
                    # If the column is not part of the joined table, add it to
                    # lhs_fields.
                    if hand_side_value.alias != self.table_alias:
                        pos = len(lhs_fields)
                        lhs_fields.append(
                            hand_side_value.as_mql(compiler, connection, as_expr=True)
                        )
                    else:
                        pos = None
                    columns.append((hand_side_value, pos))
        # Replace columns in the extra conditions with new column references
        # based on their rerouted positions in the join pipeline.
        replacements = {}
        for col, parent_pos in columns:
            target = col.target.clone()
            target.remote_field = col.target.remote_field
            column_target = Col(compiler.collection_name, target)
            if parent_pos is not None:
                column_target.is_simple_column = False
                target_col = f"${parent_template}{parent_pos}"
                column_target.target.db_column = target_col
                column_target.target.set_attributes_from_name(target_col)
            else:
                column_target.target = col.target
            replacements[col] = column_target
        return replacements

    lookup_pipeline = []
    lhs_fields = []
    rhs_fields = []
    # Add a join condition for each pair of joining fields.
    for lhs, rhs in self.join_fields:
        lhs, rhs = connection.ops.prepare_join_on_clause(
            self.parent_alias, lhs, compiler.collection_name, rhs
        )
        lhs_fields.append(lhs.as_mql(compiler, connection, as_expr=True))
        # In the lookup stage, the reference to this column doesn't include the
        # collection name.
        rhs_fields.append(rhs.as_mql(compiler, connection, as_expr=True))
    # Handle any join conditions besides matching field pairs.
    extra = self.join_field.get_extra_restriction(self.table_alias, self.parent_alias)
    extra_conditions = []
    if extra:
        replacements = _get_reroot_replacements(extra)
        extra_conditions.append(
            extra.replace_expressions(replacements).as_mql(compiler, connection)
        )
    # pushed_filter_expression is a Where expression from the outer WHERE
    # clause that involves fields from the joined (right-hand) table and
    # possibly the outer (left-hand) table. If it can be safely evaluated
    # within the $lookup pipeline (e.g., field comparisons like
    # right.status = left.id), it is "pushed" into the join's $match stage to
    # reduce the volume of joined documents. This only applies to INNER JOINs,
    # as pushing filters into a LEFT JOIN can change the semantics of the
    # result. LEFT JOINs may rely on null checks to detect missing RHS.
    if pushed_filter_expression and self.join_type == INNER:
        rerooted_replacement = _get_reroot_replacements(pushed_filter_expression)
        extra_conditions.append(
            pushed_filter_expression.replace_expressions(rerooted_replacement).as_mql(
                compiler, connection
            )
        )
    # Match the conditions:
    #   self.table_name.field1 = parent_table.field1
    # AND
    #   self.table_name.field2 = parent_table.field2
    # AND
    #   ...
    condition = {
        "$expr": {
            "$and": [
                {"$eq": [f"$${parent_template}{i}", field]} for i, field in enumerate(rhs_fields)
            ]
        }
    }
    if extra_conditions:
        condition = {"$and": [condition, *extra_conditions]}
    lookup_pipeline = [
        {
            "$lookup": {
                # The right-hand table to join.
                "from": self.table_name,
                # The pipeline variables to be matched in the pipeline's
                # expression.
                "let": {
                    f"{parent_template}{i}": parent_field
                    for i, parent_field in enumerate(lhs_fields)
                },
                "pipeline": [{"$match": condition}],
                # Rename the output as table_alias.
                "as": self.table_alias,
            }
        },
    ]
    # To avoid missing data when using $unwind, an empty collection is added if
    # the join isn't an inner join. For inner joins, rows with empty arrays are
    # removed, as $unwind unrolls or unnests the array and removes the row if
    # it's empty. This is the expected behavior for inner joins. For left outer
    # joins (LOUTER), however, an empty collection is returned.
    if self.join_type != INNER:
        lookup_pipeline.append(
            {
                "$set": {
                    self.table_alias: {
                        "$cond": {
                            "if": {
                                "$or": [
                                    {"$eq": [{"$type": f"${self.table_alias}"}, "missing"]},
                                    {"$eq": [{"$size": f"${self.table_alias}"}, 0]},
                                ]
                            },
                            "then": [{}],
                            "else": f"${self.table_alias}",
                        }
                    }
                }
            }
        )
    lookup_pipeline.append({"$unwind": f"${self.table_alias}"})
    return lookup_pipeline


def where_node(self, compiler, connection, as_expr=False):
    if self.connector == AND:
        full_needed, empty_needed = len(self.children), 1
    else:
        full_needed, empty_needed = 1, len(self.children)

    if self.connector == AND:
        operator = "$and"
    elif self.connector == XOR:
        # MongoDB doesn't support $xor, so convert:
        #   a XOR b XOR c XOR ...
        # to:
        #   (a OR b OR c OR ...) AND MOD(a + b + c + ..., 2) == 1
        # The result of an n-ary XOR is true when an odd number of operands
        # are true.
        lhs = self.__class__(self.children, OR)
        rhs_sum = reduce(
            add_operator,
            (Case(When(c, then=1), default=0) for c in self.children),
        )
        if len(self.children) > 2:
            rhs_sum = Mod(rhs_sum, 2)
        rhs = Exact(1, rhs_sum)
        return self.__class__([lhs, rhs], AND, self.negated).as_mql(
            compiler, connection, as_expr=as_expr
        )
    else:
        operator = "$or"

    children_mql = []
    for child in self.children:
        try:
            mql = child.as_mql(compiler, connection, as_expr=as_expr)
        except EmptyResultSet:
            empty_needed -= 1
        except FullResultSet:
            full_needed -= 1
        else:
            if mql:
                children_mql.append(mql)
            else:
                full_needed -= 1

        if empty_needed == 0:
            raise (FullResultSet if self.negated else EmptyResultSet)
        if full_needed == 0:
            raise (EmptyResultSet if self.negated else FullResultSet)

    if len(children_mql) == 1:
        mql = children_mql[0]
    elif len(children_mql) > 1:
        mql = {operator: children_mql}
    else:
        mql = {}

    if not mql:
        raise FullResultSet

    if self.negated and mql:
        mql = {"$not": [mql]} if as_expr else {"$nor": [mql]}

    return mql


def nothing_node(self, compiler, connection, as_expr=False):  # noqa: ARG001
    return self.as_sql(compiler, connection)


def register_nodes():
    ExtraWhere.as_mql = extra_where
    Join.as_mql = join
    NothingNode.as_mql = nothing_node
    WhereNode.as_mql = where_node
