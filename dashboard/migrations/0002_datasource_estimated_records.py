# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-10-11 17:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="datasource",
            name="estimated_records",
            field=models.PositiveIntegerField(default=0),
        )
    ]
