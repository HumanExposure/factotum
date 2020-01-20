from __future__ import absolute_import, unicode_literals

from importlib import import_module
from celery import shared_task, states

from celery.exceptions import Ignore
from django.forms import BaseForm, BaseFormSet

from celery_usertask.tasks import UserTask, usertask
from celery_filetask.tasks import FileTask, filetask

PROGRESS_STATE = "PROGRESS"


class FormTask(UserTask, FileTask):
    def shadow_name(self, args, kwargs, options):
        modulename = args[0]
        classname = args[1]
        return "%s.%s" % (modulename, classname)


@shared_task(bind=True, base=FormTask)
@usertask
@filetask
def processform(self, modulename, classname, *fargs, **fkwargs):
    formmodule = import_module(modulename)
    formclass = getattr(formmodule, classname)
    form = formclass(*fargs, task=self, **fkwargs)
    form.set_progress(description="Validating...")
    if form.is_valid():
        form.set_progress(description="Saving...")
        return form.save()
    else:
        meta = {
            "current": None,
            "total": None,
            "percent": 100,
            "exc_type": "ValidationError",
            "exc_message": "Validation failed.",
        }
        # Regular form
        if isinstance(form, BaseForm):
            meta.update({"form_errors": form.errors.get_json_data()})
        # Formset
        elif isinstance(form, BaseFormSet):
            meta.update(
                {
                    "form_errors": [error.get_json_data() for error in form.errors],
                    "non_form_errors": form.non_form_errors().get_json_data(),
                }
            )
        self.update_state(state=states.FAILURE, meta=meta)
        raise Ignore()
