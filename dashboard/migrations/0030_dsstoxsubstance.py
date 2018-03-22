# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2018-03-21 09:32
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0029_auto_20180313_1104'),
    ]

    operations = [
        migrations.CreateModel(
            name='DSSToxSubstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('true_cas', models.CharField(blank=True, max_length=50, null=True)),
                ('true_chemname', models.CharField(blank=True, max_length=500, null=True)),
                ('rid', models.CharField(blank=True, max_length=50, null=True)),
                ('sid', models.CharField(blank=True, max_length=50, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('extracted_chemical', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.ExtractedChemical')),
            ],
        ),
    ]
