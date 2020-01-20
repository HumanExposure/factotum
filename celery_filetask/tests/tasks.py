from celery import shared_task

from celery_filetask.tasks import FileTask, filetask


@shared_task(bind=True, base=FileTask)
@filetask
def getfilecontents(self, file):
    with file.open("r") as f:
        s = f.read().decode("utf-8")
    return s


@shared_task(bind=True, base=FileTask)
@filetask
def getfiletype(self, file):
    return str(type(file))


@shared_task(bind=True, base=FileTask)
@filetask
def getfilename(self, file):
    return file.name
