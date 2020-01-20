from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.base import File


def deepiter(obj, memo=None):
    memo = memo or set()
    if id(obj) not in memo:
        memo.add(id(obj))
        if isinstance(obj, dict):
            for key, value in obj.items():
                yield obj, key, value
                yield from deepiter(value, memo)
        elif isinstance(obj, list):
            for key, value in enumerate(obj):
                yield obj, key, value
                yield from deepiter(value, memo)
        elif hasattr(obj, "__dict__") and not isinstance(obj, type):
            yield from deepiter(obj.__dict__, memo)
        elif isinstance(obj, tuple):
            for value in obj:
                yield from deepiter(value, memo)


def isfilekey(deepiterout):
    obj, key, value = deepiterout
    return (
        isinstance(value, dict)
        and len(value) == 1
        and "celery_filetask_filekey" in value
    )


def isfile(deepiterout):
    obj, key, value = deepiterout
    return isinstance(value, File)


def deletefilekeys(*objs):
    storage = FileSystemStorage(location=settings.CELERY_FILETASK_ROOT)
    filekeys = filter(isfilekey, deepiter(objs))
    for _, _, filekey in filekeys:
        storage.delete(filekey["celery_filetask_filekey"]["file"])
