# Celery User Task

Emulate a Django user in your Celery tasks with [`Django-CRUM`](https://pythonhosted.org/django-crum/).

## How it works

Any call to `crum.get_current_user()` within a `UserTask` will return the user who originally called this task.

## How to use

Add the following decorator to your task:

```python
import crum

from celery_usertask.tasks import UserTask, usertask
from myproj.celery import app

@app.task(bind=True, base=UserTask)
@usertask
def task(self):
    crum.get_current_user()
    ...
```

Note: order is important and the task must have `bind=True`.

A log of all tasks and their users is also include:

```python
from celery_usertask.models import UserTaskLog

UserTaskLog.objects.all()
```
