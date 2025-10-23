Forms API reference
===================

.. module:: django_mongodb_backend.forms

Some MongoDB-specific fields are available in ``django_mongodb_backend.forms``.

``EmbeddedModelField``
----------------------

.. class:: EmbeddedModelField(model, prefix, **kwargs)

    A field which maps to a model. The field will render as a
    :class:`~django.forms.ModelForm`.

    .. attribute:: model

        This is a required argument that specifies the model class.

    .. attribute:: prefix

        This is a required argument that specifies the prefix that all fields
        in this field's subform will have so that the names don't collide with
        fields in the main form.

``EmbeddedModelArrayField``
---------------------------

.. class:: EmbeddedModelArrayField(model, *, prefix, max_num=None, extra_forms=3, **kwargs)

    A field which maps to a list of model instances. The field will render as a
    :class:`ModelFormSet <django.forms.models.BaseModelFormSet>`.

    .. attribute:: model

        This is a required argument that specifies the model class.

    .. attribute:: prefix

        This is a required argument that specifies the prefix that all fields
        in this field's formset will have so that the names don't collide with
        fields in the main form.

    .. attribute:: max_num

        This is an optional argument which specifies the maximum number of
        model instances that can be created.

    .. attribute:: extra_forms

        This argument specifies the number of blank forms that will be
        rendered by the formset.

``ObjectIdField``
-----------------

.. class:: ObjectIdField

    Stores an :class:`~bson.objectid.ObjectId`.

``SimpleArrayField``
--------------------

.. class:: SimpleArrayField(base_field, delimiter=',', length=None, max_length=None, min_length=None)

    A field which maps to an array. It is represented by an HTML ``<input>``.

    .. attribute:: base_field

        This is a required argument.

        It specifies the underlying form field for the array. This is not used
        to render any HTML, but it is used to process the submitted data and
        validate it. For example:

        .. code-block:: pycon

            >>> from django import forms
            >>> from django_mongodb_backend.forms import SimpleArrayField

            >>> class NumberListForm(forms.Form):
            ...     numbers = SimpleArrayField(forms.IntegerField())
            ...

            >>> form = NumberListForm({"numbers": "1,2,3"})
            >>> form.is_valid()
            True
            >>> form.cleaned_data
            {'numbers': [1, 2, 3]}

            >>> form = NumberListForm({"numbers": "1,2,a"})
            >>> form.is_valid()
            False

    .. attribute:: delimiter

        This is an optional argument which defaults to a comma: ``,``. This
        value is used to split the submitted data. It allows you to chain
        ``SimpleArrayField`` for multidimensional data:

        .. code-block:: pycon

            >>> from django import forms
            >>> from django_mongodb_backend.forms import SimpleArrayField

            >>> class GridForm(forms.Form):
            ...     places = SimpleArrayField(SimpleArrayField(IntegerField()), delimiter="|")
            ...

            >>> form = GridForm({"places": "1,2|2,1|4,3"})
            >>> form.is_valid()
            True
            >>> form.cleaned_data
            {'places': [[1, 2], [2, 1], [4, 3]]}

        .. note::

            The field does not support escaping of the delimiter, so be careful
            in cases where the delimiter is a valid character in the underlying
            field. The delimiter does not need to be only one character.

    .. attribute:: length

        This is an optional argument which validates that the array contains
        the stated number of items.

        ``length`` may not be specified along with ``max_length`` or
        ``min_length``.

    .. attribute:: max_length

        This is an optional argument which validates that the array does not
        exceed the stated length.

    .. attribute:: min_length

        This is an optional argument which validates that the array reaches at
        least the stated length.

    .. admonition:: User friendly forms

        ``SimpleArrayField`` is not particularly user friendly in most cases,
        however it is a useful way to format data from a client-side widget for
        submission to the server.

``SplitArrayField``
-------------------

.. class:: SplitArrayField(base_field, size, remove_trailing_nulls=False)

    This field handles arrays by reproducing the underlying field a fixed
    number of times.

    The template for this widget is located in
    ``django_mongodb_backend/templates/mongodb/widgets``. Don't forget to
    configure template loading appropriately, for example, by using a
    :class:`~django.template.backends.django.DjangoTemplates` engine with
    :setting:`APP_DIRS=True <TEMPLATES-APP_DIRS>` and
    ``"django_mongodb_backend"`` in :setting:`INSTALLED_APPS`.

    .. attribute:: base_field

        This is a required argument. It specifies the form field to be
        repeated.

    .. attribute:: size

        This is the fixed number of times the underlying field will be used.

    .. attribute:: remove_trailing_nulls

        By default, this is set to ``False``. When ``False``, each value from
        the repeated fields is stored. When set to ``True``, any trailing
        values which are blank will be stripped from the result. If the
        underlying field has ``required=True``, but ``remove_trailing_nulls``
        is ``True``, then null values are only allowed at the end, and will be
        stripped.

        Some examples::

            SplitArrayField(IntegerField(required=True), size=3, remove_trailing_nulls=False)

            ["1", "2", "3"]  # -> [1, 2, 3]
            ["1", "2", ""]  # -> ValidationError - third entry required.
            ["1", "", "3"]  # -> ValidationError - second entry required.
            ["", "2", ""]  # -> ValidationError - first and third entries required.

            SplitArrayField(IntegerField(required=False), size=3, remove_trailing_nulls=False)

            ["1", "2", "3"]  # -> [1, 2, 3]
            ["1", "2", ""]  # -> [1, 2, None]
            ["1", "", "3"]  # -> [1, None, 3]
            ["", "2", ""]  # -> [None, 2, None]

            SplitArrayField(IntegerField(required=True), size=3, remove_trailing_nulls=True)

            ["1", "2", "3"]  # -> [1, 2, 3]
            ["1", "2", ""]  # -> [1, 2]
            ["1", "", "3"]  # -> ValidationError - second entry required.
            ["", "2", ""]  # -> ValidationError - first entry required.

            SplitArrayField(IntegerField(required=False), size=3, remove_trailing_nulls=True)

            ["1", "2", "3"]  # -> [1, 2, 3]
            ["1", "2", ""]  # -> [1, 2]
            ["1", "", "3"]  # -> [1, None, 3]
            ["", "2", ""]  # -> [None, 2]
