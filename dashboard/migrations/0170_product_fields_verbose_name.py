# Generated by Django 2.2.14 on 2020-09-22 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0169_rename_extracted_chemical")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="epa_reg_number",
            field=models.CharField(
                blank=True,
                help_text="the document's EPA registration number",
                max_length=25,
                verbose_name="EPA Reg. No.",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="url",
            field=models.CharField(
                blank=True,
                help_text="Product URL",
                max_length=500,
                verbose_name="Product URL",
            ),
        ),
    ]
