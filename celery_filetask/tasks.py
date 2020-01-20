from celery import Task

from celery_filetask.contexts import fileinputs, filekeyinputs
from celery_filetask.utils import deletefilekeys


class FileTask(Task):
    def apply_async(self, args=None, kwargs=None, **options):
        with filekeyinputs(args, kwargs) as inputs:
            return super().apply_async(args=inputs[0], kwargs=inputs[1], **options)

    def _filetask_cleanup(self, args, kwargs):
        deletefilekeys(args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        self._filetask_cleanup(args, kwargs)
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        self._filetask_cleanup(args, kwargs)
        super().on_success(retval, task_id, args, kwargs)


def filetask(func):
    def _inner(self, *args, **kwargs):
        with fileinputs(args, kwargs) as inputs:
            return func(self, *inputs[0], **inputs[1])

    _inner.__name__ = func.__name__
    _inner.__module__ = func.__module__
    return _inner
