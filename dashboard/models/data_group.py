from django.apps import apps
from django.db import models
from django.urls import reverse
from model_utils import FieldTracker
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .common_info import CommonInfo
from .group_type import GroupType
from .raw_chem import RawChem


# DEPRECATED: migration 0009_auto_20171212_1405.py expects its existence
# could be used for dynamically creating filename on instantiation
# in the 'upload_to' param on th FileField
def update_filename(instance, filename):
    name_fill_space = instance.name.replace(" ", "_")
    # potential space errors in name
    name = "{0}/{0}_{1}".format(name_fill_space, filename)
    return name


# DEPRECATED: migration 0066_auto_20180927_0935.py expects its existence
def csv_upload_path(instance, filename):
    # potential space errors in name
    name = "{0}/{1}".format(instance.fs_id, filename)
    return name


class DataGroup(CommonInfo):
    """A container for registered and extracted documents, all of which
    share a common extraction script. Inherits from `CommonInfo`
    """

    name = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    downloaded_by = models.ForeignKey(
        "auth.User", on_delete=models.SET_DEFAULT, default=1
    )
    downloaded_at = models.DateTimeField()
    download_script = models.ForeignKey(
        "Script", on_delete=models.SET_NULL, default=None, null=True, blank=True
    )
    data_source = models.ForeignKey("DataSource", on_delete=models.CASCADE)
    group_type = models.ForeignKey(GroupType, on_delete=models.SET_DEFAULT, default=1)
    url = models.CharField(max_length=150, blank=True, validators=[URLValidator()])

    tracker = FieldTracker()

    @property
    def type(self):
        return str(self.group_type.code)

    @property
    def is_composition(self):
        return self.type == "CO"

    @property
    def is_supplemental_doc(self):
        return self.type == "SD"

    @property
    def is_habits_and_practices(self):
        return self.type == "HP"

    @property
    def is_functional_use(self):
        return self.type == "FU"

    @property
    def is_chemical_presence(self):
        return self.type == "CP"

    @property
    def is_hh(self):
        return self.type == "HH"

    @property
    def is_literature_monitoring(self):
        return self.type == "LM"

    @property
    def can_have_products(self):
        return bool(self.type not in ["HH", "CP", "HP", "FU"])

    def get_extract_models(self):
        """Returns the parent model class and the associated child model"""
        if self.type in ("CO", "UN"):
            m = ("ExtractedText", "ExtractedChemical")
        elif self.type == "FU":
            m = ("ExtractedText", "ExtractedFunctionalUse")
        elif self.type == "CP":
            m = ("ExtractedCPCat", "ExtractedListPresence")
        elif self.type == "HP":
            m = ("ExtractedText", "ExtractedHabitsAndPractices")
        elif self.type == "HH":
            m = ("ExtractedHHDoc", "ExtractedHHRec")
        return (apps.get_model("dashboard", m[0]), apps.get_model("dashboard", m[1]))

    def matched_docs(self):
        return self.datadocument_set.exclude(file="").count()

    def all_matched(self):
        return not self.datadocument_set.filter(file="").exists()

    def all_extracted(self):
        return not self.datadocument_set.filter(extractedtext__isnull=True).exists()

    def registered_docs(self):
        return self.datadocument_set.count()

    def extracted_docs(self):
        return self.datadocument_set.filter(extractedtext__isnull=False).count()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("data_group_edit", kwargs={"pk": self.pk})

    def get_name_as_slug(self):
        return self.name.replace(" ", "_")

    def get_extracted_template_fieldnames(self):
        extract_fields = [
            "data_document_id",
            "data_document_filename",
            "prod_name",
            "doc_date",
            "rev_num",
            "raw_category",
            "raw_cas",
            "raw_chem_name",
            "report_funcuse",
        ]
        if self.type == "FU":
            return extract_fields
        if self.type == "CO":
            return extract_fields + [
                "raw_min_comp",
                "raw_max_comp",
                "unit_type",
                "ingredient_rank",
                "raw_central_comp",
                "component",
            ]
        if self.type == "CP":
            for name in ["prod_name", "rev_num"]:
                extract_fields.remove(name)
            return extract_fields + [
                "cat_code",
                "description_cpcat",
                "cpcat_code",
                "cpcat_sourcetype",
                "component",
            ]

    def get_clean_comp_data_fieldnames(self):
        return ["id", "lower_wf_analysis", "central_wf_analysis", "upper_wf_analysis"]

    def get_product_template_fieldnames(self):
        product_fields = [
            "title",
            "upc",
            "url",
            "brand_name",
            "size",
            "color",
            "item_id",
            "parent_item_id",
            "short_description",
            "long_description",
            "thumb_image",
            "medium_image",
            "large_image",
            "model_number",
            "manufacturer",
        ]
        return product_fields

    def include_product_upload_form(self):
        return True

    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)
        if self.tracker.has_changed("group_type_id") and self.extracted_docs():
            msg = "The Group Type may not be changed once extracted documents have been associated with the group."
            raise ValidationError({"group_type": msg})

    def include_extract_form(self):
        if (
            self.type in ["FU", "CO", "CP"]
            and self.all_matched()
            and not self.all_extracted()
        ):
            return True
        else:
            return False

    def include_clean_comp_data_form(self):
        if self.type == "CO" and self.extracted_docs() > 0:
            return True
        else:
            return False

    def include_bulk_assign_form(self):
        return self.datadocument_set.filter(products=None).exists()

    def include_upload_docs_form(self):
        return not self.all_matched()

    def csv_filename(self):
        """Used in the datagroup_form.html template to display only the filename
        """
        return f"{self.get_name_as_slug()}_registered_records.csv"

    def uncurated_count(self):
        return (
            RawChem.objects.filter(dsstox__isnull=True)
            .filter(extracted_text__data_document__data_group=self)
            .count()
        )

    @property
    def uncurated(self):
        return self.uncurated_count() >= 1
