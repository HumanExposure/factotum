from django.apps import apps
from django.conf import settings
from django.db import connection
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
    def remove_trigger_sql(cls):
        default_db = settings.DATABASES["default"]["NAME"]
        sql_stmnt = (
            "SELECT Concat('DROP TRIGGER ', Trigger_Name, ';') "
            "FROM  information_schema.TRIGGERS "
            f"WHERE TRIGGER_SCHEMA = '{default_db}';"
        )
        with connection.cursor() as cursor:
            cursor.execute(sql_stmnt)
            drop_stmnts = [c[0] for c in cursor.fetchall()]
            for s in drop_stmnts:
                cursor.execute(s)

    @classmethod
    def add_trigger_sql(cls):
        with connection.cursor() as cursor:
            cursor.execute(cls.get_trigger_sql())
            print("Audit Log triggers created")

    @classmethod
    def get_trigger_sql(cls):
        """Scans all models for auditlog_fields() methods, and builds SQL string defining audit log triggers

        Returns:
            string -- a valid SQL string that can be used in a migration operation
        """
        app_label = "dashboard"
        trigger_sql = ""
        auditlog_fields = {}

        # Build dictionary of auditable fields by model
        for model in apps.all_models[app_label]:
            try:
                fields = apps.get_model(app_label, model_name=model).auditlog_fields()
                if fields is not None:
                    auditlog_fields[model] = fields
            except AttributeError:
                pass

        # Build SQL trigger string by model and auditable fields
        for model in auditlog_fields:
            table_name = app_label + "_" + model
            id = apps.get_model(app_label, model_name=model)._meta.pk.attname
            trigger_sql += f"""
                    CREATE TRIGGER  {table_name}_update_trigger
                    AFTER UPDATE ON {table_name}
                    FOR EACH ROW
                    BEGIN
            """
            for field in auditlog_fields[model]:
                trigger_sql += f"""
                    IF (NEW.{field} <> OLD.{field} or
                        (OLD.{field} IS NULL and NEW.{field} IS NOT NULL) or
                        (OLD.{field} IS NOT NULL and NEW.{field} IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            OLD.{field}, NEW.{field}, 'U', @current_user);
                    END IF;
                """
            trigger_sql += f"""
                END;

                CREATE TRIGGER  {table_name}_insert_trigger
                AFTER INSERT ON {table_name}
                FOR EACH ROW
                BEGIN
            """
            for field in auditlog_fields[model]:
                trigger_sql += f"""
                    IF NEW.{field} IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            null, NEW.{field}, 'I', @current_user);
                    END IF;
                """
            trigger_sql += f"""
                END;

                CREATE TRIGGER  {table_name}_delete_trigger
                AFTER DELETE ON {table_name}
                FOR EACH ROW
                BEGIN
            """
            for field in auditlog_fields[model]:
                trigger_sql += f"""
                    IF OLD.{field} IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.{id}, '{model}', '{field}', UTC_TIMESTAMP(),
                            OLD.{field}, null, 'D', @current_user);
                    END IF;
                """
            trigger_sql += f"""
                END;
            """
        return trigger_sql
