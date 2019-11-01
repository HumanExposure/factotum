from django.db import migrations
from django.db.models import Q


def rm_blank_chems(apps, schema_editor):
    """
    Deletes "empty" ExtractedChemical and RawChem models.

    In order to be deleted, ALL the following fields must be a null-ish value
        ExtractedChemical:
            raw_min_comp
            raw_max_comp
            report_funcuse
            ingredient_rank
            raw_central_comp
            lower_wf_analysis
            central_wf_analysis
            upper_wf_analysis
            component
        RawChem:
            raw_cas
            raw_chem_name
            rid
            dsstox

    The following fields are NOT LOOKED AT (i.e. they could be non-null, but will still be deleted):
        ExtractedChemical:
            unit_type
            weight_fraction_type
            script
        RawChem:
            extracted_text
            temp_id
            temp_obj_name
    """
    ExtractedChemical = apps.get_model("dashboard", "ExtractedChemical")
    RawChem = apps.get_model("dashboard", "RawChem")
    ec_q = (
        (Q(raw_min_comp__isnull=True) | Q(raw_min_comp=""))
        & (Q(raw_max_comp__isnull=True) | Q(raw_max_comp=""))
        & (Q(report_funcuse__isnull=True) | Q(report_funcuse=""))
        & (Q(ingredient_rank__isnull=True))
        & (Q(raw_central_comp__isnull=True) | Q(raw_central_comp=""))
        & (Q(lower_wf_analysis__isnull=True))
        & (Q(central_wf_analysis__isnull=True))
        & (Q(upper_wf_analysis__isnull=True))
        & (Q(component__isnull=True) | Q(component=""))
        & (Q(rawchem_ptr__raw_cas__isnull=True) | Q(rawchem_ptr__raw_cas=""))
        & (
            Q(rawchem_ptr__raw_chem_name__isnull=True)
            | Q(rawchem_ptr__raw_chem_name="")
        )
        & (Q(rawchem_ptr__rid__isnull=True) | Q(rawchem_ptr__rid=""))
        & (Q(rawchem_ptr__dsstox__isnull=True))
    )
    rawchem_ptr_ids = ExtractedChemical.objects.filter(ec_q).values_list(
        "rawchem_ptr_id", flat=True
    )
    RawChem.objects.filter(id__in=rawchem_ptr_ids).delete()


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0133_dsstox_validations")]

    operations = [migrations.RunPython(rm_blank_chems)]
