from celery import shared_task
from crum import get_current_user

from celery_usertask.tasks import UserTask, usertask


class ShadowNameTask(UserTask):
    def shadow_name(self, args, kwargs, options):
        return "shadow.name"


@shared_task(bind=True, base=UserTask)
@usertask
def task(self):
    return get_current_user().pk


@shared_task(bind=True, base=ShadowNameTask)
@usertask
def shadowtask(self):
    return get_current_user().pk
