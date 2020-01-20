import copy
from decimal import Decimal
import datetime

from celery_formtask.tasks import processform, PROGRESS_STATE


class FormTaskMixin:
    def __init__(self, *args, task=None, ignored_kwargs=[], **kwargs):
        self._task = task
        self._args_bak = args
        self._kwargs_bak = copy.copy(kwargs)
        for kwarg in ignored_kwargs:
            kwargs.pop(kwarg)
        super().__init__(*args, **kwargs)

    def set_progress(self, current=None, total=None, description=""):
        if self._task:
            meta_total = total or getattr(self, "formtask_total_steps", None)
            meta_description = description or getattr(
                self, "formtask_description", None
            )
            if (
                meta_total is not None
                and meta_total > 0
                and current is not None
                and current >= 0
            ):
                percent = (Decimal(current) / Decimal(meta_total)) * Decimal(100)
                meta_percent = float(round(percent, 2))
            else:
                meta_percent = None
            self._task.update_state(
                state=PROGRESS_STATE,
                meta={
                    "current": current,
                    "total": meta_total,
                    "percent": meta_percent,
                    "description": meta_description,
                    "time": datetime.datetime.utcnow(),
                },
            )

    def enqueue(self, name=None):
        opts = {"shadow": name} if name else {}
        async_result = processform.apply_async(
            args=(self.__class__.__module__, self.__class__.__name__) + self._args_bak,
            kwargs=self._kwargs_bak,
            **opts
        )
        return async_result
