# Generated by Django 2.2.1 on 2019-07-10 11:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0119_longer_definition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extractedchemical',
            name='unit_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dashboard.UnitType'),
        ),
    ]
