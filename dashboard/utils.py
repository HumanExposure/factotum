from collections.abc import MutableMapping
import zipstream

from dashboard.models import (
    PUC,
    ExtractedChemical,
    ExtractedCPCat,
    ExtractedFunctionalUse,
    ExtractedHabitsAndPractices,
    ExtractedHHDoc,
    ExtractedHHRec,
    ExtractedListPresence,
    ExtractedText,
)
from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.db import connection, transaction
from django.db.models import Aggregate
from django.db.models.sql.subqueries import InsertQuery
from django.forms.models import apply_limit_choices_to_to_formfield
from django.http import StreamingHttpResponse
from django.utils.text import get_valid_filename


class GroupConcat(Aggregate):
    """Allows Django to use the MySQL GROUP_CONCAT aggregation.

    Arguments:
        separator (str): the delimiter to use (default=',')

    Example:
        .. code-block:: python

            Pizza.objects.annotate(
                topping_str=GroupConcat(
                    'toppings',
                    separator=', ',
                    distinct=True,
                )
            )

    """

    function = "GROUP_CONCAT"
    template = "%(function)s(%(distinct)s%(expressions)s SEPARATOR '%(separator)s')"
    allow_distinct = True

    def __init__(self, expression, separator=",", **extra):
        super().__init__(expression, separator=separator, **extra)


class SimpleTree(MutableMapping):
    """A simple tree data structure.

    This has many methods similar to a dictionary.

    >>> pizza = SimpleTree()
    >>> pizza["pepperoni"] = 5
    >>> pizza["cheese", "no_pickles"] = 3
    >>> pizza["cheese", "no_mayo"] = 10
    >>> [food for food in pizza.items()]
           [(('pepperoni',), 5), (('cheese', 'no_pickles'), 3), ...]

    Values are returned by default. You can return the SimpleTree object by
    performing lookups on the "objects" interface. The "parent" attribute
    will refer to the original parent of the object.

    >>> child = pizza.objects["pizza", "cheese"]
    >>> [food for food in child.items()]
           [(('cheese', 'no_pickles'), 5), ...]
    >>> [food for food in child.parent.items()]
           [(('pepperoni',), 5), (('cheese', 'no_pickles'), 3), ...]

    You can return a dictionary representation with "asdict()".

    >>> pizza.asdict()
            {"name": "root", "children": [{"name": "pepperoni", "value": 5...}]}

    You can merge in another tree to fill in missing values.

    >>> cheese_pizza = SimpleTree()
    >>> cheese_pizza["cheese"] = 100
    >>> cheese_pizza["cheese", "no_pickles"] = "something"
    >>> pizza.merge(cheese_pizza)
    >>> pizza["cheese"]
            100
    >>> # pizza already had ("cheese", "no_pickles")
    >>> # so cheese_pizza["cheese", "no_pickles"] will not get merged in
    >>> pizza["cheese", "no_pickles"]
            3

    Attributes:
        objects (SimpleTreeObjectInterface): returns SimpleTrees
        parent (SimpleTree): the parent SimpleTree object
        name (str): the node name
        key (str): the node key
        value (any): the node value
        children (list): a list of children SimpleTree objects
    """

    class _SimpleTreeObjectInterface:
        def __init__(self, outer):
            self.outer = outer

        def __getitem__(self, keys):
            _, child = self.outer._get_or_create(keys)
            return child

    def __init__(self):
        self.parent = None
        self.name = "root"
        self.value = None
        self.children = []
        self.objects = self._SimpleTreeObjectInterface(self)

    def _get_or_create(self, keys, create=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        parent = self
        for name in keys:
            try:
                i, parent = next(
                    (i, child)
                    for i, child in enumerate(parent.children)
                    if child.name == name
                )
            except StopIteration:
                if create:
                    child = self.__class__()
                    child.parent = parent
                    child.name = name
                    parent.children.append(child)
                    i = len(parent.children) - 1
                    parent = child
                else:
                    raise KeyError(name)
        return i, parent

    @property
    def _is_item(self):
        return self.name is not None and self.value is not None

    def __setitem__(self, keys, value):
        _, child = self._get_or_create(keys, create=True)
        child.value = value

    def __getitem__(self, keys):
        _, child = self._get_or_create(keys)
        return child.value

    def __delitem__(self, keys):
        i, child = self._get_or_create(keys)
        parent = child.parent
        parent.children.pop(i)

    def __iter__(self):
        yield from self.keys()

    def __len__(self):
        return sum(1 for v in self.values())

    def items(self):
        return zip(self.keys(), self.values())

    @property
    def key(self):
        name = []
        child = self
        while child.parent is not None:
            name.insert(0, child.name)
            child = child.parent
        return tuple(name)

    def keys(self):
        if self._is_item:
            yield self.key
        for child in self.children:
            yield from child.keys()

    def values(self):
        if self._is_item:
            yield self.value
        for child in self.children:
            yield from child.values()

    def merge(self, tree):
        for child in self.children:
            if child.value is None:
                child.value = tree[child.key]
            child.merge(tree)

    def asdict(self):
        """Return a dictionary representation of the tree.
        """
        d = {"name": self.name}
        if self._is_item:
            d["value"] = self.value
        if self.children:
            d["children"] = [child.asdict() for child in self.children]
        return d


def get_extracted_models(t):
    """Returns the parent model function and the associated child model
    based on datagroup type"""
    if t == "CO" or t == "UN":
        return (ExtractedText, ExtractedChemical)
    elif t == "FU":
        return (ExtractedText, ExtractedFunctionalUse)
    elif t == "CP":
        return (ExtractedCPCat, ExtractedListPresence)
    elif t == "HP":
        return (ExtractedText, ExtractedHabitsAndPractices)
    elif t == "HH":
        return (ExtractedHHDoc, ExtractedHHRec)
    else:
        return (None, None)


def clean_dict(odict, model, translations={}, keep_nones=False):
    """Cleans out key:value pairs that aren't in the model fields
    """
    cleaned = {}
    for k, v in odict.items():
        if v is not None or keep_nones:
            translated_k = translations.get(k, k)
            try:
                model._meta.get_field(translated_k)
                cleaned[translated_k] = v
            except FieldDoesNotExist:
                continue
    return cleaned


def update_fields(odict, model):
    """Takes a dict and updates the associated fields w/in the model"""
    for f in model._meta.get_fields():
        if f.name in odict.keys():
            setattr(model, f.name, odict[f.name])


def field_for_model(model, field, **kwargs):
    """Get a form field from a model."""
    return model._meta.get_field(field).formfield(**kwargs)


def get_form_for_models(
    *args,
    fields=[],
    translations={},
    required=[],
    skip_missing=False,
    formfieldkwargs={},
):
    """Returns a form for the models and fields provided."""
    field_dict = {}
    required = set(required)
    for f in fields:
        translated_field = translations.get(f, f)
        for m in args:
            formfield = None
            try:
                k = formfieldkwargs.get(translated_field, {})
                modelfield = m._meta.get_field(translated_field)
                formfield = modelfield.formfield(**k)
                if formfield is None and modelfield.one_to_one:
                    if "queryset" in k:
                        formfield = forms.ModelChoiceField(**k)
                    else:
                        formfield = forms.ModelChoiceField(
                            queryset=modelfield.target_field.model.objects.all(), **k
                        )
                apply_limit_choices_to_to_formfield(formfield)
                if f in required:
                    formfield.required = True
                break
            except FieldDoesNotExist:
                continue
        if formfield:
            field_dict[f] = formfield
        elif not skip_missing:
            raise FieldDoesNotExist("The field '%s' was not found" % translated_field)
    return type("ModelMuxForm", (forms.Form,), field_dict)


def gather_errors(form_instance, values=False):
    """Gather errors for formsets or forms."""
    errors = []
    if type(form_instance.errors) == list:
        tmp_errors = {}
        for i, error_dict in enumerate(form_instance.errors):
            for field, error in error_dict.as_data().items():
                for e in error:
                    all_msgs = [e.message] + e.messages
                    for all_e in all_msgs:
                        if len(all_e) > 0:
                            if field == "__all__":
                                error_mesage = all_e
                            else:
                                error_mesage = "%s: %s" % (field, all_e)
                            if error_mesage in tmp_errors:
                                tmp_errors[error_mesage].append(i)
                            else:
                                tmp_errors[error_mesage] = [i]
        for error, i in tmp_errors.items():
            if values:
                field = error.split(":")[0]
                prefix = form_instance.prefix
                try:
                    uniq = set(
                        form_instance.data["%s-%d-%s" % (prefix, row, field)]
                        for row in i
                    )
                except KeyError:
                    uniq = set()
            else:
                uniq = set(str(row + 1) for row in i)
            if len(uniq) > 1:
                i_str = "values" if values else "rows"
            elif len(uniq) == 1:
                i_str = "value" if values else "row"
            else:
                i_str = ""
            if i_str:
                errors.append("%s (%s %s)" % (error, i_str, ", ".join(uniq)))
            else:
                errors.append(error)
    else:
        for field, error in form_instance.errors.as_data().items():
            if field == "__all__":
                errors.append(error[0].message)
                return errors
            for e in error:
                errors.append("%s: %s" % (field, e.message))
    if hasattr(form_instance, "non_form_errors"):
        for error in form_instance.non_form_errors().as_data():
            errors.append(error.message)

    def err_search(s):
        return any(s in e for e in errors)

    def err_filter(s):
        return list(e for e in errors if s not in e)

    def err_rep(s, r):
        return list(e.replace(s, r) for e in errors)

    if err_search("This field is required") and err_search("Please submit 1 or more"):
        errors = err_filter("Please submit 1 or more")
    errors = err_rep("Forms", "Entries")
    errors = err_rep("Form", "Entry")
    errors = err_rep("forms", "entries")
    errors = err_rep("form", "entry")
    errors = filter(lambda e: not "%(value)" in e, errors)
    return errors


def accumulate_pucs(qs):
    all_pucs = qs
    for p in qs:
        family = PUC.objects.none()
        if p.get_level() > 2:
            family = PUC.objects.filter(
                gen_cat=p.gen_cat, prod_fam=p.prod_fam, prod_type=""
            ).distinct()
        if p.get_level() > 1:
            general = PUC.objects.filter(
                gen_cat=p.gen_cat, prod_fam="", prod_type=""
            ).distinct()
            all_pucs = all_pucs | general | family
    return all_pucs


def get_missing_ids(Model, ids):
    """Evaluate which IDs do not exist in the database

    Args:
        Model: the model class or queryset to check IDs against
        ids: a sequence of integers represent the IDs to look up

    Optional args:
        filter:

    Returns:
        A list of IDs not in the database
    """
    ids_set = set(ids)
    try:
        qs = Model.objects.all()
    except AttributeError:
        qs = Model
    dbids_set = set(qs.filter(pk__in=ids_set).values_list("id", flat=True))
    return list(ids_set - dbids_set)


@transaction.atomic
def inheritance_bulk_create(models):
    """A workaround for https://code.djangoproject.com/ticket/28821

    Args:
        models: a list of models to insert

    Note that this handles less edge cases than the official
    bulk_create. For relatively simple models this will work well though.
    """
    model_class = models[0]._meta.model
    # The "chain" is a list of models leading up to and including the provided model
    chain = model_class._meta.get_parent_list() + [model_class]
    # Determine if we are setting primary keys from an auto ID or not
    top_pk_attname = chain[0]._meta.pk.attname
    if all(getattr(m, top_pk_attname) is None for m in models):
        pk_given_in_model = False
    elif all(getattr(m, top_pk_attname) is not None for m in models):
        pk_given_in_model = True
    else:
        raise ValueError("You can set all PKs or no PKs")
    parent_done = False
    last_id = 0
    for model in chain:
        meta = model._meta
        if parent_done:
            # Assign inherited primary keys
            pk_attname = meta.pk.attname
            for i, m in enumerate(models):
                top_pk = getattr(m, top_pk_attname)
                if pk_given_in_model:
                    setattr(m, pk_attname, top_pk)
                else:
                    setattr(m, pk_attname, last_id + i)
        if pk_given_in_model or last_id:
            fields = [f for f in meta.local_concrete_fields]
        else:
            fields = [f for f in meta.local_concrete_fields if not f.primary_key]
        query_gen = InsertQuery(model)
        query_gen.insert_values(fields, models)
        compiler = query_gen.get_compiler(connection=connection)
        sql_statements = query_gen.as_sql(compiler, connection)
        assert (
            len(sql_statements) == 1 and len(sql_statements[0]) == 2
        ), "We don't know how to deal with multiple queries here."
        sql_str = sql_statements[0][0]
        sql_values = sql_statements[0][1]
        with connection.cursor() as cursor:
            cursor.execute(sql_str, sql_values)
            last_id = cursor.lastrowid
        if not pk_given_in_model and not parent_done:
            for i, m in enumerate(models):
                m.pk = last_id + i
        if not parent_done:
            parent_done = True
    return models


def zip_stream(files={}, data={}, filename="file.zip"):
    """Generate a ZIP archive in a StreamingHttpResponse.

    Builds an uncompressed streaming ZIP archive rather than
    building the ZIP archive in memory then serving it.

    Args:
        files: A dictionary mapping the names of files to be placed
            in the ZIP archive to the location of the files on the
            filesystem.
        data: A dictionary mapping the names of files to be placed
            in the ZIP archive to strings or bytes containing the contents
            of the file.
        filename: A filename to optionally give the response.

    Returns:
        A django.http.StreamingHttpResponse object containing the ZIP archive.
    """
    z = zipstream.ZipFile(mode="w")
    for arcname, filesystemname in files.items():
        z.write(filesystemname, arcname)
    for arcname, datastring in data.items():
        z.writestr(arcname, datastring)
    response = StreamingHttpResponse(z, content_type="application/zip")
    response[
        "Content-Disposition"
    ] = f'attachment; filename="{get_valid_filename(filename)}"'
    return response
