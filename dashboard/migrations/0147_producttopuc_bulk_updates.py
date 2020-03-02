from django.db import migrations, models
from django.conf import settings
from django.db import connection


def drop_old_triggers(apps, schema_editor):
    default_db = settings.DATABASES["default"]["NAME"]
    sql_stmnt = (
        "SELECT Concat('DROP TRIGGER ', Trigger_Name, ';') "
        "FROM  information_schema.TRIGGERS "
        f"WHERE TRIGGER_SCHEMA = '{default_db}';"
    )
    with connection.cursor() as cursor:
        cursor.execute(sql_stmnt)
        drop_stmnts = [c[0] for c in cursor.fetchall()]
        for s in drop_stmnts:
            cursor.execute(s)


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0146_functionaluse")]

    operations = [
        migrations.AlterField(
            model_name="producttopuc",
            name="classification_method",
            field=models.CharField(
                choices=[
                    ("MA", "Manual"),
                    ("AU", "Automatic"),
                    ("RU", "Rule Based"),
                    ("MB", "Manual Batch"),
                    ("BA", "Bulk Assignment"),
                ],
                default="MA",
                max_length=2,
            ),
        ),
        # clean out all old triggers
        migrations.RunPython(drop_old_triggers, reverse_code=migrations.RunPython.noop),
    ]
