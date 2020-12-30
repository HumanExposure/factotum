# Generated by Django 2.2.14 on 2020-12-15 17:12

from django.db import migrations
import django_db_views.migration_functions
import django_db_views.operations


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0176_move_pmid_to_datadocument")]

    operations = [
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                "select distinct extracted_text_id, dsstox_id, component\n            from dashboard_rawchem\n            where dsstox_id is not null\n            group by extracted_text_id, dsstox_id, component\n            having count(extracted_text_id) > 1",
                "duplicate_chemicals",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                "", "duplicate_chemicals"
            ),
            atomic=False,
        )
    ]
