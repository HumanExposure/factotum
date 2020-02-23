from django.db import models
from django.core.exceptions import ValidationError

from .common_info import CommonInfo


class FunctionalUse(CommonInfo):
    """
    Each `FunctionalUse` record is related to a chemical record from the `RawChem`
    inheritance hierarchy. 

    A record of the `ExtractedFunctionalUse` subclass can be related to more than 
    one `FunctionalUse` record. 

    The attributes of this model used to be stored as attributes of the chemical models. 
    Migration `0145` split it out into its own schema object and migrated the old fields
    into the new table.

    """

    chem = models.ForeignKey(
        "RawChem",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name="functional_uses",
    )

    report_funcuse = models.CharField(
        "Reported functional use", max_length=255, null=False, blank=True
    )
    clean_funcuse = models.CharField(
        "Cleaned functional use", max_length=255, null=False, blank=True
    )

    def __str__(self):
        return self.report_funcuse

    def clean(self):
        if self.report_funcuse == "":
            raise ValidationError({"report_funcuse": "Please delete if no value."})

    @classmethod
    def auditlog_fields(cls):
        return ["report_funcuse", "clean_funcuse"]
