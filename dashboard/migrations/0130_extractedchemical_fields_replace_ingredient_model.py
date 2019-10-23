import dashboard.models.extracted_chemical
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0129_auto_20191011_1220")]

    operations = [
        migrations.AddField(
            model_name="extractedchemical",
            name="central_wf_analysis",
            field=models.DecimalField(
                blank=True,
                decimal_places=15,
                help_text="central weight fraction",
                max_digits=16,
                null=True,
                validators=[dashboard.models.extracted_chemical.validate_wf_analysis],
                verbose_name="Central weight fraction analysis",
            ),
        ),
        migrations.AddField(
            model_name="extractedchemical",
            name="lower_wf_analysis",
            field=models.DecimalField(
                blank=True,
                decimal_places=15,
                help_text="minimum weight fraction",
                max_digits=16,
                null=True,
                validators=[dashboard.models.extracted_chemical.validate_wf_analysis],
                verbose_name="Lower weight fraction analysis",
            ),
        ),
        migrations.AddField(
            model_name="extractedchemical",
            name="script",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="dashboard.Script",
            ),
        ),
        migrations.AddField(
            model_name="extractedchemical",
            name="upper_wf_analysis",
            field=models.DecimalField(
                blank=True,
                decimal_places=15,
                help_text="maximum weight fraction",
                max_digits=16,
                null=True,
                validators=[dashboard.models.extracted_chemical.validate_wf_analysis],
                verbose_name="Upper weight fraction analysis",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="component",
            field=models.CharField(
                blank=True,
                help_text="product component",
                max_length=200,
                null=True,
                verbose_name="Component",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="ingredient_rank",
            field=models.PositiveIntegerField(
                blank=True,
                help_text="ingredient rank",
                null=True,
                validators=[
                    dashboard.models.extracted_chemical.validate_ingredient_rank
                ],
                verbose_name="Ingredient rank",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="raw_central_comp",
            field=models.CharField(
                blank=True,
                help_text="central composition",
                max_length=100,
                null=True,
                verbose_name="Central",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="raw_max_comp",
            field=models.CharField(
                blank=True,
                help_text="maximum composition",
                max_length=100,
                null=True,
                verbose_name="Maximum",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="raw_min_comp",
            field=models.CharField(
                blank=True,
                help_text="minimum composition",
                max_length=100,
                null=True,
                verbose_name="Minimum",
            ),
        ),
        migrations.AlterField(
            model_name="extractedchemical",
            name="report_funcuse",
            field=models.CharField(
                blank=True,
                help_text="functional use",
                max_length=255,
                null=True,
                verbose_name="Reported functional use",
            ),
        ),
        # Generate the new lookup table by selecting unique combinations of
        # sid, true_cas, and true_chemname from dashboard_dsstoxsubstance
        migrations.RunSQL(
            """
            UPDATE dashboard_extractedchemical ec 
            inner join dashboard_ingredient i on 
                ec.rawchem_ptr_id = i.rawchem_ptr_id
            SET ec.central_wf_analysis = i.central_wf_analysis,
                ec.lower_wf_analysis = i.lower_wf_analysis,
                ec.upper_wf_analysis = i.upper_wf_analysis,
                ec.script_id = i.script_id
        """,
            reverse_sql=migrations.RunPython.noop,
        ),
        migrations.DeleteModel(name="Ingredient"),
    ]
