# Generated by Django 2.2.1 on 2019-10-02 08:42

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0125_extractedlistpresencetagkind")]

    operations = [
        migrations.AlterField(
            model_name="extractedchemical",
            name="report_funcuse",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Reported functional use",
            ),
        ),
        migrations.AlterField(
            model_name="extractedfunctionaluse",
            name="report_funcuse",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Reported functional use",
            ),
        ),
        migrations.AlterField(
            model_name="extractedlistpresence",
            name="report_funcuse",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                verbose_name="Reported functional use",
            ),
        ),
    ]
