# Generated by Django 2.1.7 on 2019-02-21 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0088_rawchem_extracted_text_new")]

    operations = [
        migrations.AlterField(
            model_name="puc",
            name="prod_fam",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.AlterField(
            model_name="puc",
            name="prod_type",
            field=models.CharField(blank=True, default="", max_length=100),
        ),
    ]
