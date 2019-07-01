# Generated by Django 2.2.1 on 2019-07-01 08:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dashboard', '0117_extractedlistpresencetag_kind'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datadocument',
            name='url',
            field=models.CharField(blank=True, max_length=275, null=True,
                                   validators=[django.core.validators.URLValidator()]),
        ),
        migrations.AlterField(
            model_name='datagroup',
            name='url',
            field=models.CharField(blank=True, max_length=150, validators=[django.core.validators.URLValidator()]),
        ),
        migrations.AlterField(
            model_name='datasource',
            name='url',
            field=models.CharField(blank=True, max_length=150, validators=[django.core.validators.URLValidator()]),
        ),
    ]