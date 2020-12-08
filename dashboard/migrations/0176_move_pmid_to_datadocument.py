# Generated by Django 2.2.16 on 2020-11-24 15:48

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0175_qa_summary_note")]

    operations = [
        migrations.AddField(
            model_name="datadocument",
            name="pmid",
            field=models.CharField(
                blank=True,
                max_length=20,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[0-9]*$", "PMID must be numerical"
                    )
                ],
                verbose_name="PMID",
            ),
        ),
        migrations.RunSQL(
            # populate new datadocument.pmid with existing values from other models
            sql="""
            update dashboard_datadocument
            inner join dashboard_extractedhpdoc on
             dashboard_datadocument.id = dashboard_extractedhpdoc.extractedtext_ptr_id
            set  dashboard_datadocument.pmid = dashboard_extractedhpdoc.pmid;
    
            update dashboard_datadocument
            inner join dashboard_extractedlmdoc on
             dashboard_datadocument.id = dashboard_extractedlmdoc.extractedtext_ptr_id
            set  dashboard_datadocument.pmid = dashboard_extractedlmdoc.pmid;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RemoveField(model_name="extractedhpdoc", name="pmid"),
        migrations.RemoveField(model_name="extractedlmdoc", name="pmid"),
    ]
