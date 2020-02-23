from django.core.management.commands.migrate import Command as CoreMigrateCommand
from dashboard.models import AuditLog


class Command(CoreMigrateCommand):
    def handle(self, *args, **options):
        # Do normal migrate
        super().handle(*args, **options)

        # Once the regular migrations have run and db is in its final state, add our triggers
        AuditLog.remove_trigger_sql()
        AuditLog.add_trigger_sql()
