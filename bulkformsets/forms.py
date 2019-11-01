import inspect

from django.forms import (
    BaseFormSet,
    BaseModelFormSet,
    FileField,
    formset_factory,
    formsets,
)
from django.forms.models import modelformset_factory
from django.utils.functional import cached_property

from .utils import BulkMuxDict
from .serializers import CSVReader


class InitBulkFormSet:
    """A class used to load in our custom BulkMuxDict into Django's FormSets"""

    header_fields = set()
    serializer = None
    serializer_args = []
    serializer_kwargs = {}
    filefield_kwargs = {}

    def __init__(self, *args, **kwargs):
        # Pop and set the kwargs we use outside of normal FormSets
        if "header_fields" in kwargs:
            self.header_fields = set(kwargs.pop("header_fields"))
        if "serializer" in kwargs:
            self.serializer = kwargs.pop("serializer")
        if "serializer_args" in kwargs:
            self.serializer_args = kwargs.pop("serializer_args")
        if "serializer_kwargs" in kwargs:
            self.serializer_kwargs = kwargs.pop("serializer_kwargs")
        if "filefield_kwargs" in kwargs:
            self.filefield_kwargs = kwargs.pop("filefield_kwargs")
        if "label" not in self.filefield_kwargs:
            self.filefield_kwargs["label"] = "File"
        # We always populate seializer_kwargs with max_num
        self.serializer_kwargs["max_num"] = self.max_num
        # Get the dict of passed in args matched with what the real FormSet expects
        inp = inspect.getcallargs(super().__init__, *args, **kwargs)
        # If there is already an attribute set in self, load it into the inputs.
        # Otherwise, FormSet will overwrite it on its __init__
        for i in inp:
            if hasattr(self, i):
                inp[i] = getattr(self, i)
        # We don't want to pass in self, though
        inp.pop("self")
        # BulkMuxDict needs the prefix. Try to get it from our attributes or our kwargs.
        # Otherwise, get it from the real FormSet.
        prefix = inp.get("prefix") or super().get_default_prefix()
        # Replace the real request.POST with BulkMuxDict if we have everything we need.
        fn = "%s-bulkformsetfileupload" % prefix
        if (
            all(o is not None for o in (inp["data"], inp["files"], self.serializer))
            and fn in inp["files"]
        ):
            self.bulk = self.serializer(
                inp["files"][fn], *self.serializer_args, **self.serializer_kwargs
            )
            inp["data"] = BulkMuxDict(
                inp["data"], self.bulk, self.header_fields, prefix
            )
        super().__init__(**inp)

    @property
    def header_data(self):
        """Return a dictionary of the cleaned header data.
        """
        if self.forms and self.forms[0].cleaned_data:
            return {
                k: v
                for k, v in self.forms[0].cleaned_data.items()
                if k in self.header_fields
            }
        else:
            return None

    @cached_property
    def header_form(self):
        header_form_fields = {
            k: None for k in self.form.base_fields if k not in self.header_fields
        }
        header_form_fields["bulkformsetfileupload"] = FileField(**self.filefield_kwargs)
        HeaderForm = type(
            self.form.__name__ + "Header",
            (self.form, formsets.ManagementForm),
            header_form_fields,
        )
        if self.is_bound:
            form = HeaderForm(
                self.data, self.files, auto_id=self.auto_id, prefix=self.prefix
            )
        else:
            initial = {
                formsets.TOTAL_FORM_COUNT: self.total_form_count(),
                formsets.INITIAL_FORM_COUNT: self.initial_form_count(),
                formsets.MIN_NUM_FORM_COUNT: self.min_num,
                formsets.MAX_NUM_FORM_COUNT: self.max_num,
            }
            if self.initial:
                for k, v in self.initial.items():
                    if k in self.header_fields:
                        initial[k] = v
            form = HeaderForm(auto_id=self.auto_id, prefix=self.prefix, initial=initial)
        return form


BaseBulkFormSet = type("BaseBulkFormSet", (InitBulkFormSet, BaseFormSet), {})
BaseBulkModelFormSet = type(
    "BaseBulkModelFormSet", (InitBulkFormSet, BaseModelFormSet), {}
)


def basebulkformset_factory(typename, basefactory, *args, **kwargs):
    """Create a BulkFormSet with a custom typename based on basefactory return.

    This probably shouldn't be used directly. Instead use `bulkformset_factory`,
    `csvformset_factory`, `bulkmodelformset_factory`, or `csvmodelformset_factory`.
    """
    bulk_kwargs = {
        var: kwargs.pop(var)
        for var in (
            "header_fields",
            "serializer",
            "serializer_args",
            "serializer_kwargs",
            "filefield_kwargs",
        )
        if var in kwargs
    }
    django_type = basefactory(*args, **kwargs)
    return type(
        django_type.form.__name__ + typename,
        (InitBulkFormSet, django_type),
        bulk_kwargs,
    )


def bulkformset_factory(*args, **kwargs):
    """Create a BulkFormSet.

    Refer to `django.forms.formset_factory` for an explanation on how to use. This provides some additional keyword arguments noted below.

    The serializer function is responsible for rendering the bulk file in a Python friendly way. It is invoked internally by `bulk = serializer(f, *serializer_args, **serializer_kwargs)`. Here, `f` is the Django `UploadedFile`. `bulk` must be represented as a list of dictionaries where each dictionary has keys corresponding to the field names of the `form` provided.

    It may be advantageous to return a more memory efficient immutable object from `serializer` as opposed to a list of dictionaries. An example of such an object can be seen with `bulkformsets.utils.CSVReader`.

    Required args:
        `*args`, `**kwargs`: identical to the Django equivalent
        serializer: a function that returns a list of dicts

    Optional args:
        header_fields: fields that are in the form, but not the bulk file
        serializer_args: additional positional arguments to pass to `serializer`
        serializer_kwargs: additional keyword arguments to pass to `serializer`
        filefield_kwargs: kwargs to pass to the internal FileField

    Class Properties:
        header_form: retrun the ManagementForm and the header fields as a form
        header_data: a dictionary view of cleaned data containing the header data

    Returns:
        BulkFormSet: a FormSet that works like a Django FormSet

    Notes:
        The `serializer_kwargs` will always be populated with `max_num`.
    """
    return basebulkformset_factory("BulkFormSet", formset_factory, *args, **kwargs)


def csvformset_factory(*args, **kwargs):
    """Create a CSVFormSet.

    Like `bulkformset_factory`, but there is no need to pass in a serializer.

    Serializer specific arguments:
        skip (int): [kwarg] number of initial lines to skip
        fieldnames (list of str): [kwarg] use these fieldnames instead of CSV header
        `*args`, `**kwargs`: all other arguments will be passed to `csv.reader`

    It may be useful to set skip = 1 and fieldnames to what your form field names are if the CSV header differs.
    """
    kwargs["serializer"] = CSVReader
    return basebulkformset_factory("CSVFormSet", formset_factory, *args, **kwargs)


def bulkmodelformset_factory(*args, **kwargs):
    """Create a BulkModelFormSet.

    Refer to `django.forms.model.modelformset_factory` for an explanation on how to use.
    This takes the same extra arguments as `bulkformset_factory`.
    """
    return basebulkformset_factory(
        "BulkModelFormSet", modelformset_factory, *args, **kwargs
    )


def csvmodelformset_factory(*args, **kwargs):
    """Create a BulkModelFormSet.

    Like `bulkmodelformset_factory`, but for CSVs. This takes the same extra arguments
    as `csvformset_factory`.
    """
    kwargs["serializer"] = CSVReader
    return basebulkformset_factory(
        "CSVModelFormSet", modelformset_factory, *args, **kwargs
    )
