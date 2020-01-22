from django.db import migrations

from dashboard.models import AuditLog


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0141_refactor_component_into_rawchem")]

    operations = [
        migrations.RunSQL(
            # Clear out old triggers, if they exist
            """
                DROP TRIGGER IF EXISTS raw_chem_update_trigger;
                DROP TRIGGER IF EXISTS raw_chem_insert_trigger;
                DROP TRIGGER IF EXISTS raw_chem_delete_trigger;

                DROP TRIGGER IF EXISTS extracted_chemical_update_trigger;
                DROP TRIGGER IF EXISTS extracted_chemical_insert_trigger;
                DROP TRIGGER IF EXISTS extracted_chemical_delete_trigger;

                DROP TRIGGER IF EXISTS extracted_functional_use_update_trigger;
                DROP TRIGGER IF EXISTS extracted_functional_use_insert_trigger;
                DROP TRIGGER IF EXISTS extracted_functional_use_delete_trigger;

                DROP TRIGGER IF EXISTS extracted_list_presence_update_trigger;
                DROP TRIGGER IF EXISTS extracted_list_presence_insert_trigger;
                DROP TRIGGER IF EXISTS extracted_list_presence_delete_trigger;
            """,
            reverse_sql=migrations.RunPython.noop,
        ),
        migrations.RunSQL(
            # Use dynamically generated SQL statement to generate up-to-date triggers
            AuditLog.get_trigger_sql(),
            reverse_sql=migrations.RunPython.noop,
        ),
    ]
