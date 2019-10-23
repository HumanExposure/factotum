from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0131_auditlog")]

    operations = [
        migrations.RunSQL(
            """
                DROP TRIGGER IF EXISTS extracted_chemical_update_trigger;

                CREATE TRIGGER  extracted_chemical_update_trigger
                AFTER UPDATE  ON dashboard_extractedchemical
                FOR EACH ROW
                BEGIN
                    IF (NEW.raw_min_comp <> OLD.raw_min_comp or
                        (OLD.raw_min_comp IS NULL and NEW.raw_min_comp IS NOT NULL) or
                        (OLD.raw_min_comp IS NOT NULL and NEW.raw_min_comp IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_min_comp', UTC_TIMESTAMP(),
                            OLD.raw_min_comp, NEW.raw_min_comp, 'U', @current_user);
                    END IF;

                    IF (NEW.raw_max_comp <> OLD.raw_max_comp or
                        (OLD.raw_max_comp IS NULL and NEW.raw_max_comp IS NOT NULL) or
                        (OLD.raw_max_comp IS NOT NULL and NEW.raw_max_comp IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_max_comp', UTC_TIMESTAMP(),
                            OLD.raw_max_comp, NEW.raw_max_comp, 'U', @current_user);
                    END IF;

                    IF (NEW.raw_central_comp <> OLD.raw_central_comp or
                        (OLD.raw_central_comp IS NULL and NEW.raw_central_comp IS NOT NULL) or
                        (OLD.raw_central_comp IS NOT NULL and NEW.raw_central_comp IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_central_comp', UTC_TIMESTAMP(),
                            OLD.raw_central_comp, NEW.raw_central_comp, 'U', @current_user);
                    END IF;

                    IF (NEW.unit_type_id <> OLD.unit_type_id or
                        (OLD.unit_type_id IS NULL and NEW.unit_type_id IS NOT NULL) or
                        (OLD.unit_type_id IS NOT NULL and NEW.unit_type_id IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'unit_type_id', UTC_TIMESTAMP(),
                            OLD.unit_type_id, NEW.unit_type_id, 'U', @current_user);
                    END IF;

                    IF (NEW.report_funcuse <> OLD.report_funcuse or
                        (OLD.report_funcuse IS NULL and NEW.report_funcuse IS NOT NULL) or
                        (OLD.report_funcuse IS NOT NULL and NEW.report_funcuse IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, NEW.report_funcuse, 'U', @current_user);
                    END IF;

                    IF (NEW.ingredient_rank <> OLD.ingredient_rank or
                        (OLD.ingredient_rank IS NULL and NEW.ingredient_rank IS NOT NULL) or
                        (OLD.ingredient_rank IS NOT NULL and NEW.ingredient_rank IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'ingredient_rank', UTC_TIMESTAMP(),
                            OLD.ingredient_rank, NEW.ingredient_rank, 'U', @current_user);
                    END IF;

                    IF (NEW.lower_wf_analysis <> OLD.lower_wf_analysis or
                        (OLD.lower_wf_analysis IS NULL and NEW.lower_wf_analysis IS NOT NULL) or
                        (OLD.lower_wf_analysis IS NOT NULL and NEW.lower_wf_analysis IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'lower_wf_analysis', UTC_TIMESTAMP(),
                            OLD.lower_wf_analysis, NEW.lower_wf_analysis, 'U', @current_user);
                    END IF;

                    IF (NEW.central_wf_analysis <> OLD.central_wf_analysis or
                        (OLD.central_wf_analysis IS NULL and NEW.central_wf_analysis IS NOT NULL) or
                        (OLD.central_wf_analysis IS NOT NULL and NEW.central_wf_analysis IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'central_wf_analysis', UTC_TIMESTAMP(),
                            OLD.central_wf_analysis, NEW.central_wf_analysis, 'U', @current_user);
                    END IF;

                    IF (NEW.upper_wf_analysis <> OLD.upper_wf_analysis or
                        (OLD.upper_wf_analysis IS NULL and NEW.upper_wf_analysis IS NOT NULL) or
                        (OLD.upper_wf_analysis IS NOT NULL and NEW.upper_wf_analysis IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'upper_wf_analysis', UTC_TIMESTAMP(),
                            OLD.upper_wf_analysis, NEW.upper_wf_analysis, 'U', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_chemical_insert_trigger;

                CREATE TRIGGER  extracted_chemical_insert_trigger
                AFTER INSERT ON dashboard_extractedchemical
                FOR EACH ROW
                BEGIN
                    IF NEW.raw_min_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_min_comp', UTC_TIMESTAMP(),
                            null, NEW.raw_min_comp, 'I', @current_user);
                    END IF;

                    IF NEW.raw_max_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_max_comp', UTC_TIMESTAMP(),
                            null, NEW.raw_max_comp, 'I', @current_user);
                    END IF;

                    IF NEW.raw_central_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'raw_central_comp', UTC_TIMESTAMP(),
                            null, NEW.raw_central_comp, 'I', @current_user);
                    END IF;

                    IF NEW.unit_type_id IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'unit_type_id', UTC_TIMESTAMP(),
                            null, NEW.unit_type_id, 'I', @current_user);
                    END IF;

                    IF NEW.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'report_funcuse', UTC_TIMESTAMP(),
                            null, NEW.report_funcuse, 'I', @current_user);
                    END IF;

                    IF NEW.ingredient_rank IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'ingredient_rank', UTC_TIMESTAMP(),
                            null, NEW.ingredient_rank, 'I', @current_user);
                    END IF;

                    IF NEW.lower_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'lower_wf_analysis', UTC_TIMESTAMP(),
                            null, NEW.lower_wf_analysis, 'I', @current_user);
                    END IF;

                    IF NEW.central_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'central_wf_analysis', UTC_TIMESTAMP(),
                            null, NEW.central_wf_analysis, 'I', @current_user);
                    END IF;

                    IF NEW.upper_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedchemical', 'upper_wf_analysis', UTC_TIMESTAMP(),
                            null, NEW.upper_wf_analysis, 'I', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_chemical_delete_trigger;

                CREATE TRIGGER  extracted_chemical_delete_trigger
                AFTER DELETE ON dashboard_extractedchemical
                FOR EACH ROW
                BEGIN
                    IF OLD.raw_min_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'raw_min_comp', UTC_TIMESTAMP(),
                            OLD.raw_min_comp, null, 'D', @current_user);
                    END IF;

                    IF OLD.raw_max_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'raw_max_comp', UTC_TIMESTAMP(),
                            OLD.raw_max_comp, null, 'D', @current_user);
                    END IF;

                    IF OLD.raw_central_comp IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'raw_central_comp', UTC_TIMESTAMP(),
                            OLD.raw_central_comp, null, 'D', @current_user);
                    END IF;

                    IF OLD.unit_type_id IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'unit_type_id', UTC_TIMESTAMP(),
                            OLD.unit_type_id, null, 'D', @current_user);
                    END IF;

                    IF OLD.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, null, 'D', @current_user);
                    END IF;

                    IF OLD.ingredient_rank IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'ingredient_rank', UTC_TIMESTAMP(),
                            OLD.ingredient_rank, null, 'D', @current_user);
                    END IF;

                    IF OLD.lower_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'lower_wf_analysis', UTC_TIMESTAMP(),
                            OLD.lower_wf_analysis, null, 'D', @current_user);
                    END IF;

                    IF OLD.central_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'central_wf_analysis', UTC_TIMESTAMP(),
                            OLD.central_wf_analysis, null, 'D', @current_user);
                    END IF;

                    IF OLD.upper_wf_analysis IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedchemical', 'upper_wf_analysis', UTC_TIMESTAMP(),
                            OLD.upper_wf_analysis, null, 'D', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_functional_use_update_trigger;

                CREATE TRIGGER  extracted_functional_use_update_trigger
                AFTER UPDATE ON dashboard_extractedfunctionaluse
                FOR EACH ROW
                BEGIN
                    IF (NEW.report_funcuse <> OLD.report_funcuse or
                        (OLD.report_funcuse IS NULL and NEW.report_funcuse IS NOT NULL) or
                        (OLD.report_funcuse IS NOT NULL and NEW.report_funcuse IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedfuncationaluse', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, NEW.report_funcuse, 'U', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_functional_use_insert_trigger;

                CREATE TRIGGER  extracted_functional_use_insert_trigger
                AFTER INSERT ON dashboard_extractedfunctionaluse
                FOR EACH ROW
                BEGIN
                    IF NEW.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedfuncationaluse', 'report_funcuse', UTC_TIMESTAMP(),
                            null, NEW.report_funcuse, 'I', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_functional_use_delete_trigger;

                CREATE TRIGGER  extracted_functional_use_delete_trigger
                AFTER DELETE ON dashboard_extractedfunctionaluse
                FOR EACH ROW
                BEGIN
                    IF OLD.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedfuncationaluse', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, null, 'D', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_list_presence_update_trigger;

                CREATE TRIGGER  extracted_list_presence_update_trigger
                AFTER UPDATE ON dashboard_extractedlistpresence
                FOR EACH ROW
                BEGIN
                    IF (NEW.report_funcuse <> OLD.report_funcuse or
                        (OLD.report_funcuse IS NULL and NEW.report_funcuse IS NOT NULL) or
                        (OLD.report_funcuse IS NOT NULL and NEW.report_funcuse IS NULL)) THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedlistpresence', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, NEW.report_funcuse, 'U', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_list_presence_insert_trigger;

                CREATE TRIGGER  extracted_list_presence_insert_trigger
                AFTER INSERT ON dashboard_extractedlistpresence
                FOR EACH ROW
                BEGIN
                    IF NEW.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (NEW.rawchem_ptr_id, 'extractedlistpresence', 'report_funcuse', UTC_TIMESTAMP(),
                            null, NEW.report_funcuse, 'I', @current_user);
                    END IF;
                END;


                DROP TRIGGER IF EXISTS extracted_list_presence_delete_trigger;

                CREATE TRIGGER  extracted_list_presence_delete_trigger
                AFTER DELETE ON dashboard_extractedlistpresence
                FOR EACH ROW
                BEGIN
                    IF OLD.report_funcuse IS NOT NULL THEN
                        insert into dashboard_auditlog (object_key, model_name, field_name, date_created,
                            old_value, new_value, action, user_id)
                        values (OLD.rawchem_ptr_id, 'extractedlistpresence', 'report_funcuse', UTC_TIMESTAMP(),
                            OLD.report_funcuse, null, 'D', @current_user);
                    END IF;
                END;


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
                END;

                """
        )
    ]
