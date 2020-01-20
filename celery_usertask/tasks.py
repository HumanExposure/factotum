import datetime
import uuid

from celery import shared_task, Task
from crum import get_current_user, impersonate

from celery_usertask.models import UserTaskLog


@shared_task
def cleanup(task_id):
    """Delete expired task from the UserTaskLog table."""
    UserTaskLog.objects.filter(task=task_id).delete()


class UserTask(Task):
    def apply_async(self, args=None, kwargs=None, task_id=None, shadow=None, **options):
        task_id = task_id or str(uuid.uuid4())
        # Shadow name logic aken from celery.app.task.Task.apply_async
        if self.__v2_compat__:
            shadow = shadow or self.shadow_name(
                self(), args, kwargs, dict(**options, task_id=task_id)
            )
        else:
            shadow = shadow or self.shadow_name(
                args, kwargs, dict(**options, task_id=task_id)
            )
        name = shadow or self.name
        user = get_current_user()
        UserTaskLog.objects.create(task=task_id, name=name, user=user)
        return super().apply_async(
            args=args, kwargs=kwargs, task_id=task_id, shadow=shadow, **options
        )

    def _usertask_cleanup(self, task_id):
        eta = datetime.datetime.utcnow() + self.app.conf["result_expires"]
        cleanup.apply_async(args=(task_id,), eta=eta)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self._usertask_cleanup(task_id)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        self._usertask_cleanup(task_id)
        super().on_success(retval, task_id, args, kwargs)


def usertask(func):
    def _inner(self, *args, **kwargs):
        user = UserTaskLog.objects.get(task=self.request.id).user
        with impersonate(user):
            return func(self, *args, **kwargs)

    _inner.__name__ = func.__name__
    _inner.__module__ = func.__module__
    return _inner
