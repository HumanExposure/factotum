# Generated by Django 2.2.14 on 2020-11-20 11:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0173_lm_study_type")]

    operations = [
        migrations.RemoveIndex(
            model_name="auditlog", name="dashboard_a_object__bdfb42_idx"
        ),
        migrations.AddField(
            model_name="auditlog",
            name="extracted_text",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="auditlogs",
                to="dashboard.ExtractedText",
                to_field="data_document_id",
            ),
        ),
        migrations.AddField(
            model_name="auditlog",
            name="rawchem_id",
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name="auditlog",
            name="field_name",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="auditlog",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunSQL(
            # add db level foreign key constraint on extracted_text_id and cascade delete
            sql="""
            alter table dashboard_auditlog
            add constraint `dashboard_auditlog_extracted_text_id_bf4860ab_fk_dashboard` 
            foreign key (`extracted_text_id`) REFERENCES `dashboard_extractedtext` (`data_document_id`)
            on delete cascade;
            """,
            reverse_sql="""
            alter table dashboard_auditlog
            drop foreign key `dashboard_auditlog_extracted_text_id_bf4860ab_fk_dashboard` 
            """,
        ),
        migrations.RunSQL(
            # delete data with value changed from null to empty or visa versa
            sql="""
            delete from dashboard_auditlog
            where id <> 0 and (
                (new_value = '' and old_value is null) or 
                (new_value is null and old_value = '')
            );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            # set extracted_text_id and rawchem_id field.
            # delete extracted_text_id is null as those are deleted data document
            # this will leave the field as null for deleted chem though
            sql="""
            update dashboard_auditlog al
            join dashboard_rawchem rc on al.object_key = rc.id
            set al.extracted_text_id = rc.extracted_text_id,
                al.rawchem_id = rc.id
            where al.id <> 0 and al.model_name <> 'functionaluse';
    
            update dashboard_auditlog al
            join dashboard_functionaluse fu on al.object_key = fu.id
            join dashboard_rawchem rc on fu.chem_id = rc.id
            set al.extracted_text_id = rc.extracted_text_id,
                al.rawchem_id = rc.id
            where al.id <> 0 and al.model_name = 'functionaluse';   
            
            delete from dashboard_auditlog
            where id <> 0 and extracted_text_id is null;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
