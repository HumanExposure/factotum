from django.db import migrations
from django.db.models import Q


def null_blank_chems(apps, schema_editor):
    """
    Makes unit_type NULL when ExtractedChemical.raw_min_comp,
    ExtractedChemical.raw_max_comp, and ExtractedChemical.raw_central_comp
    are NULL or blank.
    """
    ExtractedChemical = apps.get_model("dashboard", "ExtractedChemical")
    ec_q = (
        (Q(raw_min_comp__isnull=True) | Q(raw_min_comp=""))
        & (Q(raw_max_comp__isnull=True) | Q(raw_max_comp=""))
        & (Q(raw_central_comp__isnull=True) | Q(raw_central_comp=""))
    )
    ExtractedChemical.objects.filter(ec_q).update(unit_type=None)


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0135_audit_rid_trigger")]

    operations = [migrations.RunPython(null_blank_chems)]
