# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-12-26 18:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0012_datasource_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datasource',
            name='url',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]