from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0134_rm_blank_chems")]

    operations = [
        migrations.RunSQL(
            """
                DROP TRIGGER IF EXISTS raw_chem_update_trigger;

                CREATE TRIGGER  raw_chem_update_trigger
                AFTER UPDATE ON dashboard_rawchem
                FOR EACH ROW
                BEGIN
                    IF (NEW.raw_cas <> OLD.raw_cas or
                        (OLD.raw_cas IS NULL and NEW.raw_cas IS NOT NULL) or
                        (OLD.raw_cas IS NOT NULL and NEW.raw_cas IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'raw_cas', UTC_TIMESTAMP(),
                            OLD.raw_cas, NEW.raw_cas, 'U', @current_user);
                    END IF;

                    IF (NEW.raw_chem_name <> OLD.raw_chem_name or
                        (OLD.raw_chem_name IS NULL and NEW.raw_chem_name IS NOT NULL) or
                        (OLD.raw_chem_name IS NOT NULL and NEW.raw_chem_name IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'raw_chem_name', UTC_TIMESTAMP(),
                            OLD.raw_chem_name, NEW.raw_chem_name, 'U', @current_user);
                    END IF;

                    IF (NEW.rid <> OLD.rid or
                        (OLD.rid IS NULL and NEW.rid IS NOT NULL) or
                        (OLD.rid IS NOT NULL and NEW.rid IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'rid', UTC_TIMESTAMP(),
                            OLD.rid, NEW.rid, 'U', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS raw_chem_insert_trigger;

                CREATE TRIGGER  raw_chem_insert_trigger
                AFTER INSERT ON dashboard_rawchem
                FOR EACH ROW
                BEGIN
                    IF NEW.raw_cas IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'raw_cas', UTC_TIMESTAMP(),
                            null, NEW.raw_cas, 'I', @current_user);
                    END IF;

                    IF NEW.raw_chem_name IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'raw_chem_name', UTC_TIMESTAMP(),
                            null, NEW.raw_chem_name, 'I', @current_user);
                    END IF;

                    IF NEW.rid IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.id, 'rawchem', 'rid', UTC_TIMESTAMP(),
                            null, NEW.rid, 'I', @current_user);
                    END IF;
                END;

                DROP TRIGGER IF EXISTS raw_chem_delete_trigger;

                CREATE TRIGGER  raw_chem_delete_trigger
                AFTER DELETE ON dashboard_rawchem
                FOR EACH ROW
                BEGIN
                    IF OLD.raw_cas IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.id, 'rawchem', 'raw_cas', UTC_TIMESTAMP(),
                            OLD.raw_cas, null, 'D', @current_user);
                    END IF;

                    IF OLD.raw_chem_name IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.id, 'rawchem', 'raw_chem_name', UTC_TIMESTAMP(),
                            OLD.raw_chem_name, null, 'D', @current_user);
                    END IF;

                    IF OLD.rid IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.id, 'rawchem', 'rid', UTC_TIMESTAMP(),
                            OLD.rid, null, 'D', @current_user);
                    END IF;
                END;
                """
        )
    ]
