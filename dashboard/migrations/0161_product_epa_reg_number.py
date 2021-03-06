# Generated by Django 2.2.10 on 2020-04-22 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0160_doc_epa_reg_number")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="epa_reg_number",
            field=models.CharField(
                blank=True,
                help_text="the document's EPA registration number",
                max_length=25,
                verbose_name="EPA reg. no.",
            ),
        )
    ]
