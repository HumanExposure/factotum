from django.apps import apps
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    object_key = models.PositiveIntegerField(null=True)
    model_name = models.CharField(max_length=128)
    field_name = models.CharField(max_length=128, db_index=True)
    old_value = models.TextField(null=True)
    new_value = models.TextField(null=True)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(max_length=1)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.PROTECT
    )

    class Meta:
        indexes = [models.Index(fields=["object_key", "model_name", "field_name"])]

    @classmethod
    def get_trigger_sql(cls):
        """Scans all models for auditlog_fields() methods, and builds SQL string defining audit log triggers

        Returns:
            string -- a valid SQL string that can be used in a migration operation
        """
        app_label = "dashboard"
        trigger_sql = ''
        auditlog_fields = {}

        # Build dictionary of auditable fields by model
        for model in apps.all_models[app_label]:
            try:
                auditlog_fields[model] = apps.get_model(app_label, model_name=model).auditlog_fields()
            except AttributeError:
                pass

        # Build SQL trigger string by model and auditable fields
        for model in auditlog_fields:
            table_name = app_label + '_' + model
            id = 'id' if model == 'rawchem' else 'rawchem_ptr_id'
            trigger_sql += f'''
                DROP TRIGGER IF EXISTS {table_name}_update_trigger;
                CREATE TRIGGER  {table_name}_update_trigger
                AFTER UPDATE ON {table_name}
                FOR EACH ROW
                BEGIN
            '''
            for field in auditlog_fields[model]:
                trigger_sql += f'''
                    IF (NEW.{field} <> OLD.{field} or
                        (OLD.{field} IS NULL and NEW.{field} IS NOT NULL) or
                        (OLD.{field} IS NOT NULL and NEW.{field} IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            OLD.{field}, NEW.{field}, 'U', @current_user);
                    END IF;
                '''
            trigger_sql += f'''
                END;

                DROP TRIGGER IF EXISTS {table_name}_insert_trigger;
                CREATE TRIGGER  {table_name}_insert_trigger
                AFTER INSERT ON {table_name}
                FOR EACH ROW
                BEGIN
            '''
            for field in auditlog_fields[model]:
                trigger_sql += f'''
                    IF NEW.{field} IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            null, NEW.{field}, 'I', @current_user);
                    END IF;
                '''
            trigger_sql += f'''
                END;

                DROP TRIGGER IF EXISTS {table_name}_delete_trigger;
                CREATE TRIGGER  {table_name}_delete_trigger
                AFTER DELETE ON {table_name}
                FOR EACH ROW
                BEGIN
            '''
            for field in auditlog_fields[model]:
                trigger_sql += f'''
                    IF OLD.{field} IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            OLD.{field}, null, 'D', @current_user);
                    END IF;
                '''
            trigger_sql += f'''
                END;
            '''
        return trigger_sql
