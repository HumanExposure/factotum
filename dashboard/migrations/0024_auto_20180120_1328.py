# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-01-20 13:28
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0023_merge_20180120_1242")]

    operations = [
        migrations.AddField(
            model_name="extractedtext",
            name="extraction_script",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="dashboard.ExtractionScript",
            ),
        ),
        migrations.AddField(
            model_name="extractedtext",
            name="qa_checked",
            field=models.BooleanField(default=False),
        ),
    ]
