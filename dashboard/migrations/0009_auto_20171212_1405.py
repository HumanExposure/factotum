# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-12-12 19:05
from __future__ import unicode_literals

import dashboard.models.data_group
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0008_auto_20171205_0053")]

    operations = [
        migrations.CreateModel(
            name="DataDocument",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("filename", models.CharField(max_length=100)),
                ("title", models.CharField(max_length=100)),
                ("url", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "product_category",
                    models.CharField(blank=True, max_length=50, null=True),
                ),
                ("matched", models.BooleanField(default=False)),
                ("extracted", models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name="ExtractionScript",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=50)),
                (
                    "url",
                    models.TextField(
                        blank=True,
                        null=True,
                        validators=[django.core.validators.URLValidator()],
                    ),
                ),
            ],
        ),
        migrations.AlterField(
            model_name="datagroup",
            name="csv",
            field=models.FileField(
                null=True, upload_to=dashboard.models.data_group.update_filename
            ),
        ),
        migrations.AddField(
            model_name="datadocument",
            name="data_group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, to="dashboard.DataGroup"
            ),
        ),
    ]
