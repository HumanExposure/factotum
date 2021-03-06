# Generated by Django 2.2.14 on 2021-01-22 14:04

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("dashboard", "0180_product_uber_puc_view")]

    operations = [
        migrations.AddField(
            model_name="datagroup",
            name="workflow_complete",
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name="CurationStep",
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
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                (
                    "name",
                    models.CharField(
                        help_text="the curation step name", max_length=100, unique=True
                    ),
                ),
                (
                    "step_number",
                    models.PositiveSmallIntegerField(
                        help_text="the order number of the curation step to finish the workflow",
                        unique=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ("step_number",)},
        ),
        migrations.CreateModel(
            name="DataGroupCurationWorkflow",
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
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "curation_step",
                    models.ForeignKey(
                        help_text="the CurationStep object in the workflow.",
                        on_delete=django.db.models.deletion.PROTECT,
                        to="dashboard.CurationStep",
                    ),
                ),
                (
                    "step_status",
                    models.CharField(
                        choices=[("I", "Incomplete"), ("C", "Complete"), ("N", "N/A")],
                        default="I",
                        max_length=1,
                    ),
                ),
                (
                    "data_group",
                    models.ForeignKey(
                        help_text="the DataGroup object associated with the curation step.",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="curation_steps",
                        to="dashboard.DataGroup",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"unique_together": {("data_group", "curation_step")}},
        ),
        migrations.RunSQL(
            sql="""
            insert into dashboard_curationstep(name, step_number)
            values
            ('Extraction Completed', 1),
            ('QA Completed', 2),
            ('Composition Cleaned', 3),
            ('Funct. Use Cleaned', 4),
            ('Products Created', 5),
            ('PUC Assigned', 6),
            ('Keyword Tagged', 7),
            ('Chemicals Curated', 8);
            """,
            reverse_sql="",
        ),
    ]
