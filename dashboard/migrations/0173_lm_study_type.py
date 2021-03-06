# Generated by Django 2.2.16 on 2020-11-10 12:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0172_make_uberpuc_model")]

    operations = [
        migrations.AlterField(
            model_name="extractedlmdoc",
            name="study_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("Targeted", "Targeted"),
                    ("Non-Targeted", "Non-Targeted or Suspect Screening"),
                    ("Other", "Other"),
                ],
                max_length=12,
                verbose_name="Study Type",
            ),
        )
    ]
