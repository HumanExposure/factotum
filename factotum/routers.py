from django.conf import settings


class QueryLogRouter:
    """
    Routes methods dealing with elastic.models.QueryLog to
    the database defined in settings.QUERY_LOG_DATABASE
    """

    def db_for_read(self, model, **hints):
        if model._meta.model_name == "querylog" and "querylogdb" in settings.DATABASES:
            return "querylogdb"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.model_name == "querylog" and "querylogdb" in settings.DATABASES:
            return "querylogdb"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if "querylogdb" not in settings.DATABASES:
            return None
        if model_name == "querylog":
            return db == "querylogdb"
        if db == "querylogdb":
            return False
