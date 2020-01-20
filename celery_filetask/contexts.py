from abc import ABC, abstractmethod
import copy
from importlib import import_module
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from celery_filetask.utils import deepiter, isfilekey, isfile


class SwapInputs(ABC):
    def __init__(self, args, kwargs):
        self.storage = FileSystemStorage(location=settings.CELERY_FILETASK_ROOT)
        self.inputs = (
            copy.deepcopy(list(args)) if args else args,
            copy.deepcopy(kwargs) if kwargs else kwargs,
        )
        filtered_inputs = filter(self.shouldswap, deepiter(self.inputs))
        for obj, key, value in filtered_inputs:
            obj[key] = self.swap(value)

    def __enter__(self):
        return self.inputs

    def __exit__(self, exc_type, exc_value, traceback):
        pass

    @abstractmethod
    def swap(self, value):
        pass

    @staticmethod
    @abstractmethod
    def shouldswap(value):
        pass


class fileinputs(SwapInputs):
    def __exit__(self, exc_type, exc_value, traceback):
        files = filter(isfile, deepiter(self.inputs))
        for _, _, file in files:
            file.close()

    def swap(self, filekey):
        info = filekey["celery_filetask_filekey"]
        filemodule = import_module(info.pop("modulename"))
        fileclass = getattr(filemodule, info.pop("classname"))
        tmp_file = self.storage.open(info.pop("file"))
        info["file"] = tmp_file.file
        file = fileclass.__new__(fileclass)
        file.__dict__.update(info)
        return file

    @staticmethod
    def shouldswap(value):
        return isfilekey(value)


class filekeyinputs(SwapInputs):
    def swap(self, file):
        file_id = uuid.uuid4().hex
        with file.open() as f:
            self.storage.save(file_id, f)
        file_dict = dict(file.__dict__)
        file_dict["file"] = file_id
        file_dict["modulename"] = file.__class__.__module__
        file_dict["classname"] = file.__class__.__name__
        return {"celery_filetask_filekey": file_dict}

    @staticmethod
    def shouldswap(value):
        return isfile(value)
