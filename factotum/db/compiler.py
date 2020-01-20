from crum import _thread_locals
from django.db.backends.mysql.compiler import (
    SQLCompiler as MySQLCompiler,
    SQLInsertCompiler,
    SQLDeleteCompiler,
    SQLUpdateCompiler,
    SQLAggregateCompiler,
)


class SQLCompiler(MySQLCompiler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = getattr(_thread_locals, "user", False)
        if user:
            self.connection.cursor().execute("SET @current_user = %s", [user.id])
