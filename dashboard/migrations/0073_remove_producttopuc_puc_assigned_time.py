# Generated by Django 2.1.2 on 2018-11-15 17:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0072_populate_doctype_code")]

    operations = [
        migrations.RemoveField(model_name="producttopuc", name="puc_assigned_time")
    ]
