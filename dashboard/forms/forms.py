from bootstrap_datepicker_plus import DatePickerInput

from django import forms
from django.forms import BaseInlineFormSet

from django.utils.translation import ugettext_lazy as _

from dashboard.models import (
    DataDocument,
    DataGroup,
    DataSource,
    DocumentType,
    ExtractedChemical,
    ExtractedCPCat,
    ExtractedHHDoc,
    ExtractedText,
    Script,
    WeightFractionType,
    QANotes,
    Product,
    ProductToPUC,
    PUCTag,
    ExtractedFunctionalUse,
    ExtractedListPresence,
    ExtractedHHRec,
)

from dashboard.utils import get_extracted_models


class DataGroupForm(forms.ModelForm):
    required_css_class = "required"  # adds to label tag

    class Meta:
        model = DataGroup
        fields = [
            "name",
            "description",
            "url",
            "group_type",
            "downloaded_by",
            "downloaded_at",
            "download_script",
            "data_source",
            "csv",
        ]
        widgets = {"downloaded_at": DatePickerInput()}
        labels = {"csv": _("Register Records CSV File"), "url": _("URL")}

    def __init__(self, *args, **kwargs):
        qs = Script.objects.filter(script_type="DL")
        self.user = kwargs.pop("user", None)
        super(DataGroupForm, self).__init__(*args, **kwargs)
        instance = getattr(self, "instance", None)
        if instance and instance.pk:
            self.fields.pop("csv")
        else:
            self.fields["csv"].widget.attrs.update({"accept": ".csv"})
        self.fields["download_script"].queryset = qs


class ExtractionScriptForm(forms.Form):
    required_css_class = "required"  # adds to label tag
    script_selection = forms.ModelChoiceField(
        queryset=Script.objects.filter(script_type="EX"), label="Extraction Script"
    )
    weight_fraction_type = forms.ModelChoiceField(
        queryset=WeightFractionType.objects.all(),
        label="Weight Fraction Type",
        initial="1",
    )
    extract_file = forms.FileField(label="Extracted Text CSV File")

    def __init__(self, *args, **kwargs):
        self.dg_type = kwargs.pop("dg_type", 0)
        self.user = kwargs.pop("user", None)
        super(ExtractionScriptForm, self).__init__(*args, **kwargs)
        self.fields["weight_fraction_type"].widget.attrs.update(
            {"style": "height:2.75rem; !important"}
        )
        self.fields["script_selection"].widget.attrs.update(
            {"style": "height:2.75rem; !important"}
        )
        self.fields["extract_file"].widget.attrs.update({"accept": ".csv"})
        if self.dg_type in ["FU", "CP"]:
            del self.fields["weight_fraction_type"]
        self.collapsed = True


class DataSourceForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = DataSource
        fields = [
            "title",
            "url",
            "estimated_records",
            "state",
            "priority",
            "description",
        ]


class PriorityForm(forms.ModelForm):
    class Meta:
        model = DataSource
        fields = ["priority"]

    def __init__(self, *args, **kwargs):
        super(PriorityForm, self).__init__(*args, **kwargs)
        self.fields["priority"].label = ""
        self.fields["priority"].widget.attrs.update({"onchange": "form.submit();"})


class QANotesForm(forms.ModelForm):
    class Meta:
        model = QANotes
        fields = ["qa_notes"]
        widgets = {"qa_notes": forms.Textarea(attrs={"id": "qa-notes-textarea"})}
        labels = {"qa_notes": _("QA Notes (required if approving edited records)")}


class ExtractedTextQAForm(forms.ModelForm):
    required_css_class = "required"  # adds to label tag

    class Meta:
        model = ExtractedText
        fields = ["prod_name", "data_document", "qa_checked"]


class ProductLinkForm(forms.ModelForm):
    required_css_class = "required"  # adds to label tag
    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.all(), label="Data Document Type", required=True
    )

    return_url = forms.CharField()

    class Meta:
        model = Product
        fields = ["title", "manufacturer", "brand_name", "upc", "size", "color"]

    def __init__(self, *args, **kwargs):
        super(ProductLinkForm, self).__init__(*args, **kwargs)
        self.fields["return_url"].widget = forms.HiddenInput()


class ProductForm(forms.ModelForm):
    required_css_class = "required"  # adds to label tag

    class Meta:
        model = Product
        fields = [
            "title",
            "manufacturer",
            "brand_name",
            "size",
            "color",
            "model_number",
            "short_description",
            "long_description",
        ]


class ProductViewForm(ProductForm):
    class Meta(ProductForm.Meta):
        exclude = ("title", "long_description")

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].disabled = True


class BulkProductPUCForm(forms.ModelForm):
    id_pks = forms.CharField(
        label="Product Titles", widget=forms.HiddenInput(), required=True
    )

    class Meta:
        model = ProductToPUC
        fields = ["puc", "id_pks"]


class BulkProductTagForm(forms.ModelForm):
    required_css_class = "required"  # adds to label tag
    tag = forms.ModelChoiceField(queryset=PUCTag.objects.none(), label="Attribute")
    id_pks = forms.CharField(label="Product Titles", widget=forms.HiddenInput())

    class Meta:
        model = ProductToPUC
        fields = ["tag", "id_pks"]

    def __init__(self, *args, **kwargs):
        super(BulkProductTagForm, self).__init__(*args, **kwargs)
        lbl = "Select Attribute to Assign to Selected Products"
        self.fields["tag"].label = lbl


class ExtractedTextForm(forms.ModelForm):
    class Meta:
        model = ExtractedText
        fields = ["prod_name", "doc_date", "rev_num"]

        widgets = {
            "data_document": forms.HiddenInput(),
            "extraction_script": forms.HiddenInput(),
        }


class ExtractedCPCatForm(ExtractedTextForm):
    class Meta:
        model = ExtractedCPCat
        fields = [
            "doc_date",
            "cat_code",
            "description_cpcat",
            "cpcat_code",
            "cpcat_sourcetype",
        ]


class ExtractedCPCatEditForm(ExtractedCPCatForm):
    class Meta(ExtractedCPCatForm.Meta):
        fields = ExtractedCPCatForm.Meta.fields + [
            "prod_name",
            "doc_date",
            "rev_num",
            "cpcat_code",
        ]


class ExtractedHHDocForm(ExtractedTextForm):
    class Meta:
        model = ExtractedHHDoc
        fields = [
            "hhe_report_number",
            "study_location",
            "naics_code",
            "sampling_date",
            "population_gender",
            "population_age",
            "population_other",
            "occupation",
            "facility",
        ]


class ExtractedHHDocEditForm(ExtractedHHDocForm):
    class Meta(ExtractedHHDocForm.Meta):
        fields = ExtractedHHDocForm.Meta.fields + ["doc_date"]


class DocumentTypeForm(forms.ModelForm):
    class Meta:
        model = DataDocument
        fields = ["document_type"]

    def __init__(self, *args, **kwargs):
        super(DocumentTypeForm, self).__init__(*args, **kwargs)
        self.fields["document_type"].label = ""
        self.fields["document_type"].help_text = None
        self.fields["document_type"].widget.attrs.update({"onchange": "form.submit();"})


class ExtractedChemicalFormSet(BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ExtractedChemicalForm(forms.ModelForm):
    class Meta:
        model = ExtractedChemical
        fields = [
            "raw_chem_name",
            "raw_cas",
            "report_funcuse",
            "raw_min_comp",
            "raw_central_comp",
            "raw_max_comp",
            "unit_type",
            "ingredient_rank",
            "weight_fraction_type",
            "component",
        ]


class ExtractedFunctionalUseForm(forms.ModelForm):
    class Meta:
        model = ExtractedFunctionalUse
        fields = ["raw_chem_name", "raw_cas", "report_funcuse"]


class ExtractedListPresenceForm(forms.ModelForm):
    class Meta:
        model = ExtractedListPresence
        fields = ["raw_chem_name", "raw_cas", "report_funcuse", "component"]


class ExtractedHHRecForm(forms.ModelForm):
    class Meta:
        model = ExtractedHHRec
        fields = [
            "raw_chem_name",
            "raw_cas",
            "media",
            "num_measure",
            "num_nondetect",
            "sampling_method",
            "analytical_method",
        ]


def create_detail_formset(document, extra=1, can_delete=False, exclude=[], hidden=[]):
    """Returns the pair of formsets that will be needed based on group_type.
    .                       ('CO'),('CP'),('FU'),('HP'),('HH')
    Parameters
        ----------
        document : DataDocument
            The parent DataDocument
        extra : integer
            How many empty forms should be created for new records
        can_delete : boolean
            whether a delete checkbox is included
        exclude : list
            which fields to leave out of the form
        hiddent : list
            which fields to make hidden on the form
    .

    """
    group_type = document.data_group.type
    parent, child = get_extracted_models(group_type)
    extracted = hasattr(document, "extractedtext")

    def make_formset(
        parent_model,
        model,
        formset=BaseInlineFormSet,
        form=forms.ModelForm,
        exclude=exclude,
        hidden=hidden,
    ):
        formset_fields = model.detail_fields()
        if exclude:
            formset_fields = [
                in_field for in_field in formset_fields if not in_field in exclude
            ]
        # set fields to hidden if so specified
        widgets = dict(
            [
                (in_field, forms.HiddenInput())
                for in_field in formset_fields
                if in_field in hidden
            ]
        )
        return forms.inlineformset_factory(
            parent_model=parent_model,
            model=model,
            fields=formset_fields,
            formset=formset,  # this specifies a custom formset
            form=form,
            extra=extra,
            can_delete=can_delete,
            widgets=widgets,
        )

    def one():  # for chemicals or unknown
        ChemicalFormSet = make_formset(
            parent_model=parent,
            model=child,
            formset=ExtractedChemicalFormSet,
            form=ExtractedChemicalForm,
        )
        return (ExtractedTextForm, ChemicalFormSet)

    def two():  # for functional_use
        FunctionalUseFormSet = make_formset(parent, child)
        return (ExtractedTextForm, FunctionalUseFormSet)

    def three():  # for habits_and_practices
        HnPFormSet = make_formset(parent, child)
        return (ExtractedTextForm, HnPFormSet)

    def four():  # for extracted_list_presence
        ListPresenceFormSet = make_formset(parent, child)
        ParentForm = ExtractedCPCatForm if extracted else ExtractedCPCatEditForm
        return (ParentForm, ListPresenceFormSet)

    def five():  # for extracted_hh_rec
        HHFormSet = make_formset(parent, child)
        ParentForm = ExtractedHHDocForm if extracted else ExtractedHHDocEditForm
        return (ParentForm, HHFormSet)

    dg_types = {"CO": one, "UN": one, "FU": two, "HP": three, "CP": four, "HH": five}
    func = dg_types.get(group_type, lambda: None)
    return func()


class DataDocumentForm(forms.ModelForm):
    required_css_class = "required"

    class Meta:
        model = DataDocument
        fields = ["title", "subtitle", "document_type", "note", "url", "raw_category"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["raw_category"].label = "Source category"
        self.fields["document_type"].queryset = DocumentType.objects.compatible(
            self.instance
        )
