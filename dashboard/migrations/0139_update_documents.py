# Generated by Django 2.2.4 on 2019-11-21 21:31

from django.db import migrations

def update_extraction_script(apps, schema_editor):
    Text = apps.get_model("dashboard", "ExtractedText")
    Script = apps.get_model("dashboard", "Script")
    script = Script.objects.get(pk=14)
    docs = Text.objects.filter(pk__in=[1372609, 1372610])
    docs.update(extraction_script=script)
    
class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0138_field_names'),
    ]

    operations = [
        migrations.RunPython(
            update_extraction_script, reverse_code=migrations.RunPython.noop
        ),
    ]
