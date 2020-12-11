# Generated by Django 2.2.17 on 2020-12-11 10:39

from django.db import migrations
import django_db_views.migration_functions
import django_db_views.operations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0177_classification_method_fk'),
    ]

    operations = [
        django_db_views.operations.ViewRunPython(
            code=django_db_views.migration_functions.ForwardViewMigration('SELECT \n            ptp.*\n        FROM\n            (SELECT \n                dashboard_producttopuc.id, product_id, puc_id, classification_method_id, rank\n            FROM\n                dashboard_producttopuc\n            LEFT JOIN dashboard_producttopucclassificationmethod ON dashboard_producttopucclassificationmethod.id = dashboard_producttopuc.classification_method_id) ptp\n                LEFT JOIN\n            (SELECT \n                product_id, puc_id, classification_method_id, rank\n            FROM\n                dashboard_producttopuc\n            LEFT JOIN dashboard_producttopucclassificationmethod ON dashboard_producttopucclassificationmethod.id = dashboard_producttopuc.classification_method_id) ptp_rank ON ptp.product_id = ptp_rank.product_id\n                AND ptp.rank > ptp_rank.rank\n        WHERE\n            ptp_rank.rank IS NULL\n            \n            ORDER BY product_id, rank', 'product_uber_puc'),
            reverse_code=django_db_views.migration_functions.BackwardViewMigration("select id, product_id, puc_id\n          from dashboard_producttopuc\n          where (product_id, classification_method) in (\n            select product_id,\n              case\n                when min(uber_order) = 1 then 'MA'\n                when min(uber_order) = 2 then 'RU'\n                when min(uber_order) = 3 then 'MB'\n                when min(uber_order) = 4 then 'BA'\n                when min(uber_order) = 5 then 'AU'\n                else 'MA'\n              end as classification_method\n            from\n              (select product_id,\n                case\n                  when classification_method = 'MA' then 1\n                  when classification_method = 'RU' then 2\n                  when classification_method = 'MB' then 3\n                  when classification_method = 'BA' then 4\n                  when classification_method = 'AU' then 5\n                  else 1\n                end as uber_order  \n              from dashboard_producttopuc) temp\n              group by product_id\n              having min(uber_order)\n            )", 'product_uber_puc'),
            atomic=False,
        ),
    ]
