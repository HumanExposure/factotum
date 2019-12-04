from model_utils import FieldTracker
from model_utils.managers import InheritanceManager
from django.db import models
from django.apps import apps


class RawChem(models.Model):
    extracted_text = models.ForeignKey(
        "ExtractedText",
        related_name="rawchem",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    raw_cas = models.CharField(
        "Raw CAS", max_length=100, null=True, blank=True, help_text="Raw CAS"
    )
    raw_chem_name = models.CharField(
        "Raw chemical name",
        max_length=1300,
        null=True,
        blank=True,
        help_text="Raw chemical name",
    )
    temp_id = models.IntegerField(default=0, null=True, blank=True)
    temp_obj_name = models.CharField(max_length=255, null=True, blank=True)

    rid = models.CharField(max_length=50, null=True, blank=True, help_text="RID")

    dsstox = models.ForeignKey(
        "DSSToxLookup",
        related_name="curated_chemical",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    objects = InheritanceManager()

    tracker = FieldTracker()

    def __str__(self):
        return str(self.raw_chem_name) if self.raw_chem_name else ""

    @property
    def sid(self):
        """If there is no DSSToxLookup record via the 
        curated_chemical relationship, it evaluates to boolean False """
        try:
            return self.curated_chemical.sid
        except AttributeError:
            return False

    @property
    def data_group_id(self):
        return str(self.extracted_text.data_document.data_group_id)

    def clean(self):
        def whitespace(fld):
            if fld:
                return fld.startswith(" ") or fld.endswith(" ")
            else:
                return False

        if whitespace(self.raw_cas):
            self.raw_cas = self.raw_cas.strip()
        if whitespace(self.raw_chem_name):
            self.raw_chem_name = self.raw_chem_name.strip()

    @property
    def true_cas(self):
        return self.dsstox.true_cas if self.dsstox else None

    @property
    def true_chemname(self):
        return self.dsstox.true_chemname if self.dsstox else None

    @property
    def rendered_chemname(self):
        return self.dsstox.true_chemname if self.dsstox else self.raw_chem_name

    @property
    def rendered_cas(self):
        return self.dsstox.true_cas if self.dsstox else self.raw_cas
