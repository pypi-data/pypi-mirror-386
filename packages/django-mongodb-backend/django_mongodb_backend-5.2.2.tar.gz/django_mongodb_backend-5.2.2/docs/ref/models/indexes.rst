=====================
Model index reference
=====================

.. module:: django_mongodb_backend.indexes
   :synopsis: Database indexes for MongoDB.

Some MongoDB-specific :doc:`indexes <django:ref/models/indexes>`, for use on a
model's :attr:`Meta.indexes <django.db.models.Options.indexes>` option, are
available in ``django_mongodb_backend.indexes``.

Search indexes
==============

MongoDB creates these indexes asynchronously, however, Django's
:class:`~django.db.migrations.operations.AddIndex` and
:class:`~django.db.migrations.operations.RemoveIndex` operations will wait
until the index is created or deleted so that the database state is
consistent in the operations that follow. Adding indexes may take seconds or
minutes, depending on the size of the collection.

.. versionchanged:: 5.2.1

    The aforementioned waiting was added.

``SearchIndex``
---------------

.. class:: SearchIndex(fields=(), field_mappings=None, name=None, analyzer=None, search_analyzer=None)

    Creates a basic :doc:`search index <atlas:atlas-search/index-definitions>`
    on the given field(s).

    Some fields such as :class:`~django.db.models.DecimalField` aren't
    supported. See the :ref:`Atlas documentation <atlas:bson-data-chart>` for a
    complete list of unsupported data types.

    Use ``field_mappings`` (instead of ``fields``) to create a complex search
    index. ``field_mappings`` is a dictionary that maps field names to index
    options. It corresponds to ``definition["mappings"]["fields"]`` in the
    :ref:`atlas:fts-static-mapping-examples`.

    If ``name`` isn't provided, one will be generated automatically. If you
    need to reference the name in your search query and don't provide your own
    name, you can lookup the generated one using ``Model._meta.indexes[0].name``
    (substituting the name of your model as well as a different list index if
    your model has multiple indexes).

    Use ``analyzer`` and ``search_analyzer`` to configure the indexing and
    searching :doc:`analyzer <atlas:atlas-search/analyzers>`. If these options
    aren't provided, the server defaults to ``lucene.standard``. It corresponds
    to ``definition["analyzer"]`` and ``definition["searchAnalyzer"]`` in the
    :ref:`atlas:fts-static-mapping-examples`.

    .. versionchanged:: 5.2.2

        The ``field_mappings``, ``analyzer``, and ``search_analyzer`` arguments
        were added.

``VectorSearchIndex``
---------------------

.. class:: VectorSearchIndex(*, fields=(), name=None, similarities)

    A subclass of :class:`SearchIndex` that creates a :doc:`vector search index
    <atlas:atlas-vector-search/vector-search-type>` on the given field(s).

    The index must reference at least one vector field: an :class:`.ArrayField`
    with a :attr:`~.ArrayField.base_field` of
    :class:`~django.db.models.FloatField` or
    :class:`~django.db.models.IntegerField` and a :attr:`~.ArrayField.size`. It
    cannot reference an :class:`.ArrayField` of any other type.

    It may also have other fields to filter on, provided the field stores
    ``boolean``, ``date``, ``objectId``, ``numeric``, ``string``, or ``uuid``.

    Available values for the required ``similarities`` keyword argument are
    ``"cosine"``, ``"dotProduct"``, and ``"euclidean"`` (see
    :ref:`atlas:avs-similarity-functions` for how to choose). You can provide
    this value either a string, in which case that value will be applied to all
    vector fields, or a list or tuple of values with a similarity corresponding
    to each vector field.
