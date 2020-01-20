# Celery File Task

Easily include a Django `File` in your Celery task.

## How it works

You have a few options if a Celery task depends on a file input:
1. Pickle the file and store it with the task message
2. Save the file and rewrite your task to open the saved file

The first is less than ideal: often the message broker is in-memory and storing large files in-memory is a bad idea.

This app automates the second option. If using it, whenever a file is found *anywhere* in your task arguments:
1. The `File` is found by recursively searching your arguments.
2. The file is saved with a UUID filename in a special folder.
3. The `File` is replaced by a dictionary describing how to reopen this file.
4. The Celery worker receiving this task will swap back in the real file.

## How to use

First, set the variable `CELERY_FILETASK_ROOT` in your Django `settings.py` file to where you want to store the files. Then add the following decorator to your task:

```python
from celery_filetask.tasks import FileTask, filetask
from myproj.celery import app

@app.task(bind=True, base=FileTask)
@filetask
def task(self, dict_with_file):
    ...
```

Note: order is important and the task must have `bind=True`.
