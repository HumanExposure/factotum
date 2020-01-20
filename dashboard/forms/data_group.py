import os
import uuid
import zipfile
from pathlib import Path
from datetime import datetime
from django.utils import timezone

from django import forms
from django.conf import settings
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import CharField, Value as V

from django.db.models.functions import Cast, Concat

from bulkformsets import BaseBulkFormSet, CSVReader
from celery_formtask.forms import FormTaskMixin

from dashboard.models import (
    DataDocument,
    Product,
    ProductDocument,
    Script,
    DocumentType,
    ExtractedChemical,
    DataGroup,
    RawChem,
    ExtractedText,
    ExtractedCPCat,
    UnitType,
    ExtractedFunctionalUse,
    ExtractedListPresence,
    WeightFractionType,
)

from dashboard.utils import (
    clean_dict,
    get_extracted_models,
    get_form_for_models,
    field_for_model,
    field_for_model,
    get_missing_ids,
    inheritance_bulk_create,
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


class ProductCSVForm(forms.Form):
    """ A form based on the Product object
    but with the addition of data_document_id and
    data_document_filename fields
    """

    data_document_id = field_for_model(ProductDocument, "document_id")
    data_document_filename = field_for_model(DataDocument, "filename")
    title = field_for_model(Product, "title")
    upc = field_for_model(Product, "upc", required=False)
    url = field_for_model(Product, "url")
    brand_name = field_for_model(Product, "brand_name")
    size = field_for_model(Product, "size")
    color = field_for_model(Product, "color")
    item_id = field_for_model(Product, "item_id")
    parent_item_id = field_for_model(Product, "parent_item_id")
    short_description = field_for_model(Product, "short_description")
    long_description = field_for_model(Product, "long_description")
    thumb_image = field_for_model(Product, "thumb_image")
    medium_image = field_for_model(Product, "medium_image")
    large_image = field_for_model(Product, "large_image")
    model_number = field_for_model(Product, "model_number")
    manufacturer = field_for_model(Product, "manufacturer")


class ProductBulkCSVFormSet(DGFormSet):
    """
    Multiple products can be created for a single document.
    If user attempts to upload product data for a document
    which already has an associated product, a new product
    is created with the newly uploaded data (rather than
    trying to insert data into the existing product record).
    If a user uploads a product file which includes multiple
    rows for a single data document ID, each row should be
    assumed to be a different product for that document
    """

    prefix = "products"
    serializer = CSVReader
    form = ProductCSVForm

    def clean(self, *args, **kwargs):
        header = list(self.bulk.fieldnames)
        header_cols = [
            "data_document_id",
            "data_document_filename",
        ] + DataGroup.get_product_template_fieldnames(self)
        if header != header_cols:
            raise forms.ValidationError(f"CSV column titles should be {header_cols}")

        # Iterate over the formset to accumulate the UPCs and check for duplicates
        upcs = [f.cleaned_data["upc"] for f in self.forms if f.cleaned_data.get("upc")]

        seen = {}
        # The original list of duplicated UPCs should include all the ones
        # already in the database that appear in the uploaded file. All the
        # new UPCs are added as well in order to check for in-file duplication
        self.dupe_upcs = list(
            Product.objects.filter(upc__in=upcs)
            .values_list("upc", flat=True)
            .distinct()
        )
        for x in upcs:
            if x not in seen:
                seen[x] = 1
            else:
                if seen[x] == 1:
                    self.dupe_upcs.append(x)
                seen[x] += 1

    def save(self):
        rejected_docids = []
        reports = ""
        added_products = 0

        for f in self.forms:
            f.cleaned_data["created_at"] = datetime.now()
            product_dict = clean_dict(f.cleaned_data, Product)
            # Reject the Product if its UPC already exists in the database
            # or if it was identified as an internal duplicate above
            if product_dict.get("upc") in self.dupe_upcs:
                # if the UPC is already in the database, reject
                # this product and report it. It does not invalidate
                # the formset, though
                rejected_docids.append(f.cleaned_data["data_document_id"].pk)
            else:
                if not product_dict.get("upc"):
                    # mint a new stub_x UPC if there was none provided
                    product_dict["upc"] = Product.objects.next_upc()
                # add the new product to the database
                product = Product(**product_dict)
                product.save()
                # once the product is created, it can be linked to
                # a DataDocument via the ProductDocument table
                productdocument = ProductDocument(
                    product=product, document=f.cleaned_data["data_document_id"]
                )
                productdocument.save()
                added_products += 1

        if len(rejected_docids) > 0:
            reports = f"The following records had existing or duplicated UPCs and were not added: "
            reports += ", ".join("%d" % i for i in rejected_docids)

        return added_products, reports


class BaseExtractFileForm(forms.Form):
    extraction_script = forms.IntegerField(required=True)
    data_document_id = forms.IntegerField(required=True)
    doc_date = field_for_model(ExtractedText, "doc_date")
    raw_category = field_for_model(DataDocument, "raw_category")
    raw_cas = field_for_model(RawChem, "raw_cas")
    raw_chem_name = field_for_model(RawChem, "raw_chem_name")

    def clean(self):
        super().clean()
        data = self.cleaned_data
        # Rename fields
        data["extraction_script_id"] = data.pop("extraction_script")
        data["extracted_text_id"] = data.get("data_document_id")
        # Validate model
        params = clean_dict(self.cleaned_data, ExtractedText)
        ExtractedText(**params).clean()


class FunctionalUseExtractFileForm(BaseExtractFileForm):
    prod_name = field_for_model(ExtractedText, "prod_name")
    rev_num = field_for_model(ExtractedText, "rev_num")
    report_funcuse = field_for_model(ExtractedFunctionalUse, "report_funcuse")

    def clean(self):
        super().clean()
        params = clean_dict(self.cleaned_data, ExtractedFunctionalUse)
        obj = ExtractedFunctionalUse(**params)
        obj.clean()
        obj.validate_unique()


class CompositionExtractFileForm(BaseExtractFileForm):
    prod_name = field_for_model(ExtractedText, "prod_name")
    rev_num = field_for_model(ExtractedText, "rev_num")
    weight_fraction_type = forms.IntegerField(required=False)
    raw_min_comp = field_for_model(ExtractedChemical, "raw_min_comp")
    raw_max_comp = field_for_model(ExtractedChemical, "raw_max_comp")
    unit_type = forms.IntegerField(required=False)
    ingredient_rank = field_for_model(ExtractedChemical, "ingredient_rank")
    raw_central_comp = field_for_model(ExtractedChemical, "raw_central_comp")
    component = field_for_model(ExtractedChemical, "component")
    report_funcuse = field_for_model(ExtractedChemical, "report_funcuse")

    def clean(self):
        super().clean()
        data = self.cleaned_data
        # Rename fields
        data["weight_fraction_type_id"] = data.pop("weight_fraction_type")
        data["unit_type_id"] = data.pop("unit_type")
        # Validate model
        params = clean_dict(self.cleaned_data, ExtractedChemical)
        obj = ExtractedChemical(**params)
        obj.clean()
        obj.validate_unique()


class ChemicalPresenceExtractFileForm(BaseExtractFileForm):
    cat_code = field_for_model(ExtractedCPCat, "cat_code")
    description_cpcat = field_for_model(ExtractedCPCat, "description_cpcat")
    cpcat_code = field_for_model(ExtractedCPCat, "cpcat_code")
    cpcat_sourcetype = field_for_model(ExtractedCPCat, "cpcat_sourcetype")
    report_funcuse = field_for_model(ExtractedListPresence, "report_funcuse")
    component = field_for_model(ExtractedListPresence, "component")

    def clean(self):
        super().clean()
        data = self.cleaned_data
        params = clean_dict(data, ExtractedCPCat)
        obj = ExtractedCPCat(**params)
        obj.clean()
        obj.validate_unique()
        params = clean_dict(data, ExtractedListPresence)
        obj = ExtractedListPresence(**params)
        obj.clean()
        obj.validate_unique()


class ExtractFileFormSet(FormTaskMixin, DGFormSet):
    prefix = "extfile"
    header_fields = ["weight_fraction_type", "extraction_script"]
    serializer = CSVReader

    def __init__(self, *args, dgpk=None, **kwargs):
        # We seem to be doing nothing with DataDocument.filename even though it's
        # being collected.
        dg = DataGroup.objects.get(pk=dgpk)
        self.dg = dg
        if dg.type == "FU":
            self.form = FunctionalUseExtractFileForm
        elif dg.type == "CO":
            self.form = CompositionExtractFileForm
            self.header_fields.append("weight_fraction_type")
            # For the template render
            self.weight_fraction_type_choices = [
                (str(wf.pk), str(wf)) for wf in WeightFractionType.objects.all()
            ]
        elif dg.type == "CP":
            self.form = ChemicalPresenceExtractFileForm
        # For the template render
        self.extraction_script_choices = [
            (str(s.pk), str(s))
            for s in Script.objects.filter(script_type="EX").filter(qa_begun=False)
        ]
        super().__init__(*args, dgpk=dgpk, ignored_kwargs=["dgpk"], **kwargs)

    def clean(self):
        validation_errors = []
        # We're now CPU bound on this call, not SQL bound. Make for a more fun problem.
        Parent, Child = get_extracted_models(self.dg.type)
        unique_parent_ids = set(f.cleaned_data["data_document_id"] for f in self.forms)
        # Check that extraction_script is valid
        extraction_script_id = self.forms[0].cleaned_data["extraction_script_id"]
        if not Script.objects.filter(
            script_type="EX", pk=extraction_script_id
        ).exists():
            err = forms.ValidationError("Invalid extraction script selection.")
            validation_errors.append(err)
        # Check that unit_type is valid
        unit_type_ids = (
            f.cleaned_data["unit_type_id"]
            for f in self.forms
            if f.cleaned_data.get("unit_type_id") is not None
        )
        bad_ids = get_missing_ids(UnitType, unit_type_ids)
        if bad_ids:
            err_str = 'The following "unit_type"s were not found: '
            err_str += ", ".join("%d" % i for i in bad_ids)
            err = forms.ValidationError(err_str)
            validation_errors.append(err)
        # Check that weight_fraction_type is valid
        weight_fraction_type_ids = (
            f.cleaned_data["weight_fraction_type_id"]
            for f in self.forms
            if f.cleaned_data.get("weight_fraction_type_id") is not None
        )
        bad_ids = get_missing_ids(WeightFractionType, weight_fraction_type_ids)
        if bad_ids:
            err_str = 'The following "weight_fraction_type"s were not found: '
            err_str += ", ".join("%d" % i for i in bad_ids)
            err = forms.ValidationError(err_str)
            validation_errors.append(err)
        # Check that the data_document_id are all valid
        datadocument_dict = DataDocument.objects.filter(data_group=self.dg).in_bulk(
            unique_parent_ids
        )
        if len(datadocument_dict) != len(unique_parent_ids):
            bad_ids = unique_parent_ids - datadocument_dict.keys()
            err_str = (
                'The following "data_document_id"s were not found for this data group: '
            )
            err_str += ", ".join("%d" % i for i in bad_ids)
            err = forms.ValidationError(err_str)
            validation_errors.append(err)
        # Check that parent fields do not conflict (OneToOne check)
        if hasattr(Parent, "cat_code"):
            oto_field = "cat_code"
        elif hasattr(Parent, "prod_name"):
            oto_field = "prod_name"
        else:
            oto_field = None
        if oto_field:
            unique_parent_oto_fields = set(
                (f.cleaned_data["data_document_id"], f.cleaned_data[oto_field])
                for f in self.forms
            )
            if len(unique_parent_ids) != len(unique_parent_oto_fields):
                unseen_parents = set(unique_parent_ids)
                bad_ids = []
                for i, _ in unique_parent_oto_fields:
                    if i in unseen_parents:
                        unseen_parents.remove(i)
                    else:
                        bad_ids.append(i)
                err_str = (
                    'The following "data_document_id"s got unexpected "%s"s (must be 1:1): '
                    % oto_field
                )
                err_str += ", ".join("%d" % i for i in bad_ids)
                err = forms.ValidationError(err_str)
                validation_errors.append(err)
        if validation_errors:
            raise forms.ValidationError(validation_errors)
        # Make the DataDocument, Parent, and Child objects and validate them
        parent_dict = Parent.objects.in_bulk(unique_parent_ids)
        unseen_parents = set(unique_parent_ids)
        for form in self.forms:
            data = form.cleaned_data
            pk = data["data_document_id"]
            # Parent and DataDocument
            if pk in unseen_parents:
                # DataDocument updates
                datadocument = datadocument_dict[pk]
                new_raw_category = data["raw_category"]
                old_raw_category = datadocument.raw_category
                if new_raw_category != old_raw_category:
                    datadocument.raw_category = new_raw_category
                    datadocument.clean(skip_type_check=True)
                    datadocument._meta.created_fields = {}
                    datadocument._meta.updated_fields = {
                        "raw_category": {
                            "old": old_raw_category,
                            "new": new_raw_category,
                        }
                    }
                else:
                    datadocument._meta.created_fields = {}
                    datadocument._meta.updated_fields = {}
                # Parent creates
                parent_params = clean_dict(data, Parent)
                if pk not in parent_dict:
                    parent = Parent(**parent_params)
                    parent._meta.created_fields = parent_params
                    parent._meta.updated_fields = {}
                # Parent updates
                else:
                    parent = parent_dict[pk]
                    parent._meta.created_fields = {}
                    parent._meta.updated_fields = {}
                    for field, new_value in parent_params.items():
                        old_value = getattr(parent, field)
                        if new_value != old_value:
                            setattr(parent, field, new_value)
                            parent._meta.updated_fields[field] = {
                                "old_value": old_value,
                                "new_value": new_value,
                            }
                # Mark this parent as seen
                unseen_parents.remove(pk)
            else:
                parent = None
                datadocument = None
            # Child creates
            child_params = clean_dict(data, Child)
            # Only include children if relevant data is attached
            if child_params.keys() - {"extracted_text_id", "weight_fraction_type_id"}:
                child = Child(**child_params)
                child._meta.created_fields = child_params
                child._meta.updated_fields = {}
            else:
                child = None
            # Store in dictionary
            data["datadocument"] = datadocument
            data["parent"] = parent
            data["child"] = child

    def save(self):
        datadocuments = [
            f.cleaned_data["datadocument"]
            for f in self.forms
            if f.cleaned_data["datadocument"]
        ]
        parents = [
            f.cleaned_data["parent"] for f in self.forms if f.cleaned_data["parent"]
        ]
        children = [
            f.cleaned_data["child"] for f in self.forms if f.cleaned_data["child"]
        ]
        with transaction.atomic():
            # Update DataDocument and Parent
            for objs in (datadocuments, parents):
                updated_objs = [o for o in objs if o._meta.updated_fields]
                updated_fields = {"updated_at"}
                for obj in updated_objs:
                    updated_fields |= set(obj._meta.updated_fields.keys())
                    obj.updated_at = timezone.now()
                if updated_objs:
                    model = updated_objs[0]._meta.model
                    model.objects.bulk_update(updated_objs, updated_fields)
            # Create Parent and Child
            for objs in (parents, children):
                created_objs = [o for o in objs if o._meta.created_fields]
                if created_objs:
                    inheritance_bulk_create(created_objs)
            # Store CSV
            fs = FileSystemStorage(os.path.join(settings.MEDIA_URL, str(self.dg.fs_id)))
            fs.save(
                str(self.dg) + "_extracted.csv",
                self.files["extfile-bulkformsetfileupload"],
            )
        return len(self.forms)


class CleanCompForm(forms.ModelForm):
    ExtractedChemical_id = forms.IntegerField(required=True)
    script_id = forms.IntegerField(required=True)

    class Meta:
        model = ExtractedChemical
        fields = ["lower_wf_analysis", "central_wf_analysis", "upper_wf_analysis"]

    def clean(self):
        super().clean()
        params = clean_dict(self.cleaned_data, ExtractedChemical)
        obj = ExtractedChemical(**params)
        obj.clean()
        # Ensure data is provided.
        central_wf_analysis = self.cleaned_data.get("central_wf_analysis")
        lower_wf_analysis = self.cleaned_data.get("lower_wf_analysis")
        upper_wf_analysis = self.cleaned_data.get("upper_wf_analysis")
        if not (central_wf_analysis or lower_wf_analysis or upper_wf_analysis):
            raise forms.ValidationError("No weight fraction data provided.")


class CleanCompFormSet(DGFormSet):
    prefix = "cleancomp"
    header_fields = ["script_id"]
    serializer = CSVReader
    form = CleanCompForm

    def __init__(self, dg, *args, **kwargs):
        self.dg = dg
        self.script_choices = [
            (str(s.pk), str(s)) for s in Script.objects.filter(script_type="DC")
        ]
        super().__init__(*args, **kwargs)

    def clean(self):
        # Ensure ExtractedChemical_id's are valid
        self.cleaned_ids = [
            f.cleaned_data["ExtractedChemical_id"]
            for f in self.forms
            if "ExtractedChemical_id" in f.cleaned_data
        ]
        bad_ids = get_missing_ids(
            ExtractedChemical.objects.filter(
                extracted_text__data_document__data_group=self.dg
            ),
            self.cleaned_ids,
        )
        if bad_ids:
            bad_ids_str = ", ".join(str(i) for i in bad_ids)
            raise forms.ValidationError(
                f"The following IDs do not exist in ExtractedChemicals for this data group: {bad_ids_str}"
            )
        # Ensure script ID is valid
        script_id = self.forms[0].cleaned_data.get("script_id")
        if (
            script_id
            and not Script.objects.filter(script_type="DC", pk=script_id).exists()
        ):
            raise forms.ValidationError(f"Invalid script selection.")

    def save(self):
        now = datetime.now()
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
                chem.script_id = form.cleaned_data["script_id"]
                chem.updated_at = timezone.now()
                chems.append(chem)
            ExtractedChemical.objects.bulk_update(
                chems,
                [
                    "upper_wf_analysis",
                    "central_wf_analysis",
                    "lower_wf_analysis",
                    "script_id",
                    "updated_at",
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
        before getting to any form-specific errors.
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
