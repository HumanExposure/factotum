# Generated by Django 2.2.14 on 2021-01-12 13:47

from django.db import migrations
import django_db_views.migration_functions
import django_db_views.operations


class Migration(migrations.Migration):

    dependencies = [("dashboard", "0179_puc_classification_method")]

    operations = [
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration(
                """
                 SELECT ptp.*
                 FROM (
                     SELECT ptp.*, cm.rank
                     FROM dashboard_producttopuc ptp
                     LEFT JOIN dashboard_producttopucclassificationmethod cm ON cm.id = ptp.classification_method_id
                 ) ptp
                 LEFT JOIN (
                     SELECT product_id, puc_id, classification_method_id, rank
                     FROM dashboard_producttopuc ptp
                     LEFT JOIN dashboard_producttopucclassificationmethod cm ON cm.id = ptp.classification_method_id
                 ) ptp_rank ON ptp.product_id = ptp_rank.product_id AND ptp.rank > ptp_rank.rank
                 WHERE ptp_rank.rank IS NULL
                """,
                "product_uber_puc",
            ),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration(
                """
                 SELECT ptp.*
                 FROM (
                     SELECT ptp.id, product_id, puc_id, classification_method_id, rank
                     FROM dashboard_producttopuc ptp
                     LEFT JOIN dashboard_producttopucclassificationmethod cm ON cm.id = ptp.classification_method_id
                 ) ptp
                 LEFT JOIN (
                     SELECT product_id, puc_id, classification_method_id, rank
                     FROM dashboard_producttopuc ptp
                     LEFT JOIN dashboard_producttopucclassificationmethod cm ON cm.id = ptp.classification_method_id
                 ) ptp_rank ON ptp.product_id = ptp_rank.product_id AND ptp.rank > ptp_rank.rank
                 WHERE ptp_rank.rank IS NULL
                """,
                "product_uber_puc",
            ),
            atomic=False,
        )
    ]
