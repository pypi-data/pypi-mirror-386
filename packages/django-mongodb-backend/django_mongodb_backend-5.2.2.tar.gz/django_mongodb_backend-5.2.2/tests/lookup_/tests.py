from bson import SON
from django.test import TestCase

from django_mongodb_backend.test import MongoTestCaseMixin

from .models import Book, Number


class NumericLookupTests(MongoTestCaseMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.objs = Number.objects.bulk_create(Number(num=x) for x in range(5))
        # Null values should be excluded in less than queries.
        cls.null_number = Number.objects.create()

    def test_lt(self):
        self.assertQuerySetEqual(Number.objects.filter(num__lt=3), self.objs[:3])

    def test_lte(self):
        self.assertQuerySetEqual(Number.objects.filter(num__lte=3), self.objs[:4])

    def test_empty_range(self):
        with self.assertNumQueries(0):
            self.assertQuerySetEqual(Number.objects.filter(num__range=[3, 1]), [])

    def test_full_range(self):
        with self.assertNumQueries(1) as ctx:
            self.assertQuerySetEqual(
                Number.objects.filter(num__range=[None, None]), [self.null_number, *self.objs]
            )
        query = ctx.captured_queries[0]["sql"]
        self.assertAggregateQuery(
            query, "lookup__number", [{"$addFields": {"num": "$num"}}, {"$sort": SON([("num", 1)])}]
        )


class RegexTests(MongoTestCaseMixin, TestCase):
    def test_mql(self):
        # $regexMatch must not cast the input to string, otherwise MongoDB
        # can't use the field's indexes.
        with self.assertNumQueries(1) as ctx:
            list(Book.objects.filter(title__regex="Moby Dick"))
        query = ctx.captured_queries[0]["sql"]
        self.assertAggregateQuery(
            query,
            "lookup__book",
            [{"$match": {"title": {"$regex": "Moby Dick", "$options": ""}}}],
        )


class LookupMQLTests(MongoTestCaseMixin, TestCase):
    def test_eq(self):
        with self.assertNumQueries(1) as ctx:
            list(Book.objects.filter(title="Moby Dick"))
        self.assertAggregateQuery(
            ctx.captured_queries[0]["sql"], "lookup__book", [{"$match": {"title": "Moby Dick"}}]
        )

    def test_in(self):
        with self.assertNumQueries(1) as ctx:
            list(Book.objects.filter(title__in=["Moby Dick"]))
        self.assertAggregateQuery(
            ctx.captured_queries[0]["sql"],
            "lookup__book",
            [{"$match": {"title": {"$in": ("Moby Dick",)}}}],
        )

    def test_eq_and_in(self):
        with self.assertNumQueries(1) as ctx:
            list(Book.objects.filter(title="Moby Dick", isbn__in=["12345", "56789"]))
        self.assertAggregateQuery(
            ctx.captured_queries[0]["sql"],
            "lookup__book",
            [{"$match": {"$and": [{"isbn": {"$in": ("12345", "56789")}}, {"title": "Moby Dick"}]}}],
        )
