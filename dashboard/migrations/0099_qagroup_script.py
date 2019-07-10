# Generated by Django 2.1.2 on 2019-03-22 10:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0098_add_cpcat_qa_flag")]

    operations = [
        migrations.AlterField(
            model_name="qagroup",
            name="extraction_script",
            field=models.ForeignKey(
                limit_choices_to={"script_type": "EX"},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="qa_group",
                to="dashboard.Script",
            ),
        )
    ]
