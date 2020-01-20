from django.db.backends.mysql.base import *

# Workaround for thread-local Django-CRUM (relevant for Celery)
DatabaseOperations.compiler_module = "factotum.db.compiler"
