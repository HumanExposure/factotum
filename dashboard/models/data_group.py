import os
import uuid
from pathlib import PurePath

from django.apps import apps
from django.conf import settings
from django.db import models
from django.urls import reverse
from model_utils import FieldTracker
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from .common_info import CommonInfo
from .group_type import GroupType
from .raw_chem import RawChem


# could be used for dynamically creating filename on instantiation
# in the 'upload_to' param on th FileField
def update_filename(instance, filename):
    name_fill_space = instance.name.replace(" ", "_")
    # potential space errors in name
    name = "{0}/{0}_{1}".format(name_fill_space, filename)
    return name


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
    fs_id = models.UUIDField(default=uuid.uuid4, editable=False)
    csv = models.FileField(upload_to=csv_upload_path, null=True)
    zip_file = models.CharField(max_length=100)
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

    def save(self, *args, **kwargs):
        super(DataGroup, self).save(*args, **kwargs)

    def matched_docs(self):
        return self.datadocument_set.filter(matched=True).count()

    def all_matched(self):
        return not self.datadocument_set.filter(matched=False).exists()

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

    def get_dg_folder(self):
        uuid_dir = f"{settings.MEDIA_ROOT}{str(self.fs_id)}"

        # this needs to handle missing csv files
        if bool(self.csv.name):
            # parse the media folder from the penultimate piece of csv file path
            p = PurePath(self.csv.path)
            csv_folder = p.parts[-2]
            csv_fullfolderpath = f"{settings.MEDIA_ROOT}{csv_folder}"

        if os.path.isdir(uuid_dir):
            return uuid_dir  # UUID-based folder
        elif bool(self.csv.name) and os.path.isdir(csv_fullfolderpath):
            return csv_fullfolderpath  # csv path-based folder
        else:
            return "no_folder_found"

    @property
    def dg_folder(self):
        """This is a "falsy" property. If the folder cannot be found,
        dg.dg_folder evaluates to boolean False """
        if self.get_dg_folder() != "no_folder_found":
            return self.get_dg_folder()
        else:
            return False

    @property
    def csv_url(self):
        """This is a "falsy" property. If the csv file cannot be found,
        dg.csv_url evaluates to boolean False """
        try:
            self.csv.size
            csv_url = self.csv.url
        except ValueError:
            csv_url = False
        except:
            csv_url = False
        return csv_url

    @property
    def zip_url(self):
        """This is a "falsy" property. If the zip file cannot be found,
        dg.zip_url evaluates to boolean False """
        if self.get_zip_url() != "no_path_found":
            return self.get_zip_url
        else:
            return False

    def get_zip_url(self):
        # the path if the data group's folder was built from a UUID:
        uuid_path = f"{self.get_dg_folder()}/{str(self.fs_id)}.zip"
        # path if the data group's folder was built from old name-based method
        zip_file_path = f"{self.get_dg_folder()}/{self.get_name_as_slug()}.zip"
        if os.path.isfile(uuid_path):  # it is a newly-added data group
            zip_url = uuid_path
        elif os.path.isfile(zip_file_path):  # it is a pre-UUID data group
            zip_url = zip_file_path
        else:
            zip_url = "no_path_found"
        return zip_url

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
        return self.datadocument_set.filter(matched=False).exists()

    def csv_filename(self):
        """Used in the datagroup_form.html template to display only the filename
        """
        return self.csv.name.split("/")[-1]

    def uncurated_count(self):
        return (
            RawChem.objects.filter(dsstox__isnull=True)
            .filter(extracted_text__data_document__data_group=self)
            .count()
        )

    @property
    def uncurated(self):
        return self.uncurated_count() >= 1
