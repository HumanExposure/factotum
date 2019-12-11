from six import text_type

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F

from .script import Script
from .raw_chem import RawChem
from .unit_type import UnitType
from .common_info import CommonInfo
from .weight_fraction_type import WeightFractionType


def validate_ingredient_rank(value):
    if value < 1 or value > 999:
        raise ValidationError(
            (f"Quantity {value} is not allowed"), params={"value": value}
        )


def validate_wf_analysis(value):
    if value < 0 or value > 1:
        raise ValidationError(
            (f"Quantity {value} must be between 0 and 1"), params={"value": value}
        )


class ExtractedChemical(CommonInfo, RawChem):
    raw_min_comp = models.CharField(
        "Minimum",
        max_length=100,
        null=True,
        blank=True,
        help_text="minimum composition",
    )
    raw_max_comp = models.CharField(
        "Maximum",
        max_length=100,
        null=True,
        blank=True,
        help_text="maximum composition",
    )
    unit_type = models.ForeignKey(
        UnitType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name="Unit type",
    )
    report_funcuse = models.CharField(
        "Reported functional use",
        max_length=255,
        null=True,
        blank=True,
        help_text="functional use",
    )
    weight_fraction_type = models.ForeignKey(
        WeightFractionType,
        on_delete=models.PROTECT,
        null=True,
        default="1",
        verbose_name="Weight fraction type",
    )
    ingredient_rank = models.PositiveIntegerField(
        "Ingredient rank",
        null=True,
        blank=True,
        validators=[validate_ingredient_rank],
        help_text="ingredient rank",
    )
    raw_central_comp = models.CharField(
        "Central",
        max_length=100,
        null=True,
        blank=True,
        help_text="central composition",
    )
    lower_wf_analysis = models.DecimalField(
        "Lower weight fraction analysis",
        max_digits=16,
        decimal_places=15,
        null=True,
        blank=True,
        validators=[validate_wf_analysis],
        help_text="minimum weight fraction",
    )
    central_wf_analysis = models.DecimalField(
        "Central weight fraction analysis",
        max_digits=16,
        decimal_places=15,
        null=True,
        blank=True,
        validators=[validate_wf_analysis],
        help_text="central weight fraction",
    )
    upper_wf_analysis = models.DecimalField(
        "Upper weight fraction analysis",
        max_digits=16,
        decimal_places=15,
        null=True,
        blank=True,
        validators=[validate_wf_analysis],
        help_text="maximum weight fraction",
    )
    script = models.ForeignKey(
        to=Script, on_delete=models.CASCADE, null=True, blank=True
    )
    component = models.CharField(
        "Component",
        max_length=200,
        null=True,
        blank=True,
        help_text="product component",
    )

    class Meta:
        ordering = (F("ingredient_rank").asc(nulls_last=True),)

    def clean(self):
        error_dict = {}
        ut = bool(self.unit_type_id)
        minc = self.raw_min_comp is not None
        cenc = self.raw_central_comp is not None
        maxc = self.raw_max_comp is not None
        minwf = self.lower_wf_analysis is not None
        cenwf = self.central_wf_analysis is not None
        maxwf = self.upper_wf_analysis is not None
        # Don't allow the unit_type to be empty if there are raw_min_comp,
        # raw_central_comp, or raw_max_comp values.
        if ~ut & (minc | cenc | maxc):
            err_msg = "There must be a unit type if a composition value is provided."
            error_dict["unit_type"] = [err_msg]
        # Only accept central XOR (min and max), if any
        err_msg = (
            "Central %s value cannot be defined with "
            "minimum value and maximum value."
        )
        if (cenc & minc) | (cenc & maxc):
            error_dict["raw_central_comp"] = [err_msg % "composition"]
        if (cenwf & minwf) | (cenwf & maxwf):
            error_dict["central_wf_analysis"] = [err_msg % "weight fraction"]
        # Ensure both max and min are filled, if either
        err_msg = "Both minimum and maximimum %s values must be provided, not just one."
        if (minc | maxc) & ~(minc & maxc):
            if minc:
                error_dict["raw_max_comp"] = [err_msg % "composition"]
            else:
                error_dict["raw_min_comp"] = [err_msg % "composition"]
        if (minwf | maxwf) & ~(minwf & maxwf):
            if minwf:
                error_dict["upper_wf_analysis"] = [err_msg % "weight fraction"]
            else:
                error_dict["lower_wf_analysis"] = [err_msg % "weight fraction"]
        # Raise validation errors
        if error_dict:
            raise ValidationError(error_dict)

    @classmethod
    def detail_fields(cls):
        return [
            "extracted_text",
            "raw_chem_name",
            "raw_cas",
            "unit_type",
            "raw_min_comp",
            "raw_central_comp",
            "raw_max_comp",
            "ingredient_rank",
            "report_funcuse",
            "weight_fraction_type",
            "rawchem_ptr",
            "component",
        ]

    def get_datadocument_url(self):
        return self.extracted_text.data_document.get_absolute_url()

    @property
    def data_document(self):
        return self.extracted_text.data_document

    def get_extractedtext(self):
        return self.extracted_text

    @property
    def sid(self):
        if hasattr(self, "curated_chemical") and self.curated_chemical is not None:
            return self.curated_chemical.sid
        else:
            return None

    def __get_label(self, field):
        return text_type(self._meta.get_field(field).verbose_name)

    @property
    def raw_min_comp_label(self):
        return self.__get_label("raw_min_comp")

    @property
    def raw_central_comp_label(self):
        return self.__get_label("raw_central_comp")

    @property
    def raw_max_comp_label(self):
        return self.__get_label("raw_max_comp")

    @property
    def unit_type_label(self):
        return self.__get_label("unit_type")

    @property
    def report_funcuse_label(self):
        return self.__get_label("report_funcuse")

    @property
    def weight_fraction_type_label(self):
        return self.__get_label("weight_fraction_type")

    @property
    def ingredient_rank_label(self):
        return self.__get_label("ingredient_rank")

    @property
    def component_label(self):
        return self.__get_label("component")
