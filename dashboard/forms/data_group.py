import uuid
import zipfile
from pathlib import Path
from datetime import datetime

from django import forms
from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import CharField, Value as V
from django.db.models.functions import Cast, Concat

from bulkformsets import BaseBulkFormSet, CSVReader
from dashboard.models import (
    DataDocument,
    Product,
    ProductDocument,
    Script,
    DocumentType,
    ExtractedChemical,
)

from dashboard.utils import (
    clean_dict,
    get_extracted_models,
    get_form_for_models,
    get_invalid_ids,
)


class DGFormSet(BaseBulkFormSet):
    extra = 0
    can_order = False
    can_delete = False
    min_num = 1
    max_num = 50000
    absolute_max = 50000
    validate_min = True
    validate_max = True


class UploadDocsForm(forms.Form):
    prefix = "uploaddocs"
    documents = forms.FileField()

    def __init__(self, dg, *args, **kwargs):
        self.dg = dg
        super().__init__(*args, **kwargs)

    def clean(self):
        if len(self.files.getlist("%s-documents" % self.prefix)) > 600:
            raise forms.ValidationError("Please limit upload to 600 files.")
        uploaded_filenames = set(
            f.name for f in self.files.getlist("%s-documents" % self.prefix)
        )
        self.datadocuments = DataDocument.objects.filter(
            data_group=self.dg, filename__in=uploaded_filenames
        )
        if not self.datadocuments.exists():
            raise forms.ValidationError(
                "There are no matching filenames in the directory selected."
            )

    def save(self):
        store = settings.MEDIA_URL + str(self.dg.fs_id)
        fs = FileSystemStorage(store + "/pdf")
        upd_list = []
        doc_dict = {d.name: d for d in self.files.getlist("%s-documents" % self.prefix)}
        # TODO: we'll have dangling files if there is a failure in here
        with zipfile.ZipFile(self.dg.zip_file, "a", zipfile.ZIP_DEFLATED) as zf:
            for datadocument in self.datadocuments:
                docfile = doc_dict[datadocument.filename]
                afn = datadocument.get_abstract_filename()
                fs.save(afn, docfile)
                zf.write(store + "/pdf/" + afn, afn)
                datadocument.matched = True
                upd_list.append(datadocument)
        DataDocument.objects.bulk_update(self.datadocuments, ["matched"])
        return self.datadocuments.count()


class ExtractFileFormSet(DGFormSet):
    prefix = "extfile"
    header_fields = ["weight_fraction_type", "extraction_script"]
    serializer = CSVReader

    def __init__(self, dg, *args, **kwargs):
        # We seem to be doing nothing with DataDocument.filename even though it's
        # being collected. It will still be validated against though.
        self.dg = dg
        Parent, Child = get_extracted_models(dg.type)
        fields = dg.get_extracted_template_fieldnames() + self.header_fields
        self.form = get_form_for_models(
            Parent,
            Child,
            DataDocument,
            fields=fields,
            translations={"data_document_filename": "filename"},
            skip_missing=True,
        )
        super().__init__(*args, **kwargs)

    def clean(self):
        Parent, Child = get_extracted_models(self.dg.type)
        if hasattr(Parent, "cat_code"):
            oto_field = "cat_code"
        elif hasattr(Parent, "prod_name"):
            oto_field = "prod_name"
        else:
            return
        invalid_oto = []
        # First check against values in the database
        for p in Parent.objects.filter(
            pk__in=(f.cleaned_data["data_document_id"].pk for f in self.forms)
        ):
            for f in self.forms:
                if f.cleaned_data["data_document_id"].pk == p.pk and f.cleaned_data[
                    oto_field
                ] != getattr(p, oto_field):
                    invalid_oto.append((p.pk, getattr(p, oto_field)))
        # Now check against values within the form
        for i, f1 in enumerate(self.forms):
            for f2 in self.forms[i:]:
                if (
                    f1.cleaned_data["data_document_id"].pk
                    == f2.cleaned_data["data_document_id"].pk
                    and f1.cleaned_data[oto_field] != f2.cleaned_data[oto_field]
                ):
                    invalid_oto.append(
                        (
                            f1.cleaned_data["data_document_id"],
                            f1.cleaned_data[oto_field],
                        )
                    )

        if invalid_oto:
            err_str = (
                'The following "data_document_id"s got unexpected "%s"s (must be 1:1): '
                % oto_field
            )
            err_str += ", ".join(
                '%d (expected "%s" to be "%s")' % (o[0].pk, oto_field, o[1])
                for o in invalid_oto
            )
            raise forms.ValidationError(err_str)

    def save(self):
        Parent, Child = get_extracted_models(self.dg.type)
        raw_cat_map = {
            f.cleaned_data["data_document_id"].pk: f.cleaned_data["raw_category"]
            for f in self.forms
        }
        parent_collected_ids = set()
        with transaction.atomic():
            # DataDocument update
            docs = []
            for obj in DataDocument.objects.select_for_update().filter(
                pk__in=(f.cleaned_data["data_document_id"].pk for f in self.forms)
            ):
                obj.raw_category = raw_cat_map[obj.pk]
                docs.append(obj)
            DataDocument.objects.bulk_update(docs, ["raw_category"])
            # There's no real good way to do bulk creates/updates for inherited models
            # Parent update or create
            for f in self.forms:
                if f.cleaned_data["data_document_id"].pk not in parent_collected_ids:
                    params = clean_dict(f.cleaned_data, Parent)
                    params["data_document_id"] = f.cleaned_data["data_document_id"].pk
                    try:
                        obj = Parent.objects.get(
                            data_document_id=params["data_document_id"]
                        )
                        params.pop("data_document_id")
                        for key, value in params.items():
                            setattr(obj, key, value)
                        obj.save()
                    except Parent.DoesNotExist:
                        obj = Parent(**params)
                        obj.save()
                    parent_collected_ids.add(obj)
            # Child create
            for f in self.forms:
                params = clean_dict(f.cleaned_data, Child)
                params["extracted_text_id"] = f.cleaned_data["data_document_id"].pk
                Child.objects.create(**params)
            # Store CSV
            fs = FileSystemStorage(settings.MEDIA_URL + str(self.dg.fs_id))
            fs.save(
                str(self.dg) + "_extracted.csv",
                self.files["extfile-bulkformsetfileupload"],
            )
        return len(self.forms)


class CleanCompForm(forms.ModelForm):

    ExtractedChemical_id = forms.IntegerField(required=True)

    class Meta:
        model = ExtractedChemical
        fields = [
            "lower_wf_analysis",
            "central_wf_analysis",
            "upper_wf_analysis",
            "script",
        ]

    def __init__(self, *args, **kwargs):
        super(CleanCompForm, self).__init__(*args, **kwargs)
        self.fields["script"].queryset = Script.objects.filter(script_type="DC")
        self.fields["script"].required = True

    def clean(self):
        super().clean()
        central_wf_analysis = self.cleaned_data.get("central_wf_analysis")
        lower_wf_analysis = self.cleaned_data.get("lower_wf_analysis")
        upper_wf_analysis = self.cleaned_data.get("upper_wf_analysis")
        if central_wf_analysis and (lower_wf_analysis or upper_wf_analysis):
            self.add_error(
                None,
                (
                    "If central_wf_analysis is populated, neither lower_wf_analysis"
                    " nor upper_wf_analysis may be populated."
                ),
            )
        if not central_wf_analysis and (not lower_wf_analysis or not upper_wf_analysis):
            self.add_error(
                None,
                (
                    "If central_wf_analysis is blank, both lower_wf_analysis and"
                    " upper_wf_analysis must be populated."
                ),
            )


class CleanCompFormSet(DGFormSet):
    prefix = "cleancomp"
    header_fields = ["script"]
    serializer = CSVReader

    def __init__(self, dg, *args, **kwargs):
        self.dg = dg
        self.form = CleanCompForm
        super().__init__(*args, **kwargs)

    def clean(self):
        self.cleaned_ids = [
            f.cleaned_data["ExtractedChemical_id"]
            for f in self.forms
            if "ExtractedChemical_id" in f.cleaned_data
        ]
        bad_ids = get_invalid_ids(ExtractedChemical, self.cleaned_ids)
        bad_ids_str = ", ".join(str(i) for i in bad_ids)
        if bad_ids:
            raise forms.ValidationError(
                f"The following IDs do not exist in ExtractedChemicals: {bad_ids_str}"
            )

    def save(self):
        with transaction.atomic():
            database_chemicals = ExtractedChemical.objects.select_for_update().in_bulk(
                self.cleaned_ids
            )
            chems = []
            for form in self.forms:
                pk = form.cleaned_data["ExtractedChemical_id"]
                chem = database_chemicals[pk]
                chem.upper_wf_analysis = form.cleaned_data.get("upper_wf_analysis")
                chem.central_wf_analysis = form.cleaned_data.get("central_wf_analysis")
                chem.lower_wf_analysis = form.cleaned_data.get("lower_wf_analysis")
                chem.script = form.cleaned_data["script"]
                chems.append(chem)
            ExtractedChemical.objects.bulk_update(
                chems,
                [
                    "upper_wf_analysis",
                    "central_wf_analysis",
                    "lower_wf_analysis",
                    "script",
                ],
            )
        return len(self.forms)


class BulkAssignProdForm(forms.Form):
    prefix = "bulkassignprod"

    def __init__(self, dg, *args, **kwargs):
        self.dg = dg
        self.count = DataDocument.objects.filter(data_group=dg, product=None).count()
        super().__init__(*args, **kwargs)

    def save(self):
        docs = DataDocument.objects.filter(data_group=self.dg, products=None).values(
            "pk", "title", "extractedtext__prod_name"
        )
        tmp_uuid = str(uuid.uuid4())
        prods = []
        for doc in docs:
            # We temporarily set the upc to a UUID so we can locate it later.
            # This way we can then update these with "stub_{pk}". This significantly
            # reduces the number of database calls.
            upc = "%s-%d" % (tmp_uuid, doc["pk"])
            if doc["extractedtext__prod_name"]:
                title = doc["extractedtext__prod_name"]
            elif doc["title"]:
                title = doc["title"] + " stub"
            else:
                title = "unknown"
            prods.append(Product(title=title, upc=upc))
        with transaction.atomic():
            Product.objects.bulk_create(prods)
            created_prods = Product.objects.select_for_update().filter(
                upc__startswith=tmp_uuid
            )
            prod_docs = []
            for p in created_prods:
                prod_docs.append(
                    ProductDocument(product_id=p.pk, document_id=int(p.upc[37:]))
                )
            created_prods.update(upc=Concat(V("stub_"), Cast("id", CharField())))
            ProductDocument.objects.bulk_create(prod_docs)
        return self.count


class RegisterRecordsFormSet(DGFormSet):
    prefix = "register"
    header_fields = ["data_group"]
    serializer = CSVReader

    def __init__(self, dg, *args, **kwargs):
        self.dg = dg
        self.form = DataDocumentCSVForm
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        """Errors raised here are exposed in non_form_errors() and will be rendered
        before getting to and form-specific errors.
        """
        header = list(self.bulk.fieldnames)
        header_cols = ["filename", "title", "document_type", "url", "organization"]
        if header != header_cols:
            raise forms.ValidationError(f"CSV column titles should be {header_cols}")
        if not any(self.errors):
            values = set()
            for form in self.forms:
                value = form.cleaned_data.get("filename")
                if value in values:
                    raise forms.ValidationError(
                        f'Duplicate "filename" values for "{value}" are not allowed.'
                    )
                values.add(value)

    def save(self):
        with transaction.atomic():
            new_docs = []
            now = datetime.now()
            for f in self.forms:
                f.cleaned_data["created_at"] = now
                obj = DataDocument(**f.cleaned_data)
                new_docs.append(obj)
            DataDocument.objects.bulk_create(new_docs)
        made = DataDocument.objects.filter(created_at=now, data_group=self.dg)
        text = "DataDocument_id,filename,title,document_type,url,organization\n"
        for doc in made:
            items = [
                str(doc.pk),
                doc.filename,
                doc.title,
                doc.document_type.code,
                doc.url if doc.url else "",
                doc.organization,
            ]
            text += ",".join(items) + "\n"
        with open(self.dg.csv.path, "w") as f:
            myfile = File(f)
            myfile.write("".join(text))
        uid = str(self.dg.fs_id)
        new_zip_path = Path(settings.MEDIA_URL) / uid / (uid + ".zip")
        zf = zipfile.ZipFile(str(new_zip_path), "w", zipfile.ZIP_DEFLATED)
        zf.close()
        self.dg.zip_file = new_zip_path
        self.dg.save()
        return len(self.forms)


class DocTypeFormField(forms.ModelChoiceField):
    def clean(self, value):
        if value:
            try:
                return DocumentType.objects.get(code=value)
            except:
                raise forms.ValidationError(
                    f"'{value}' is not a valid DocumentType code."
                )
        else:
            return DocumentType.objects.get(code="UN")


class DataDocumentCSVForm(forms.ModelForm):
    class Meta:
        model = DataDocument
        fields = [
            "data_group",
            "filename",
            "title",
            "document_type",
            "url",
            "organization",
        ]
        field_classes = {"document_type": DocTypeFormField}
