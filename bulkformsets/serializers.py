import csv
import itertools as it
import io

from django.forms import formsets


class CSVReader:
    """Like csv.DictReader, except includes a low memory __getitem__ and __len__."""

    def __init__(self, f, *args, **kwargs):
        max_num = kwargs.pop("max_num", 2 * formsets.DEFAULT_MAX_NUM)
        skip = kwargs.pop("skip", 0)
        fieldnames = kwargs.pop("fieldnames", None)
        if type(f.file) is io.StringIO:
            self.f = f
        elif isinstance(f.file, io.BufferedIOBase):
            self.f = io.TextIOWrapper(f.file, encoding="utf-8-sig", newline="")
        else:
            raise ValueError("Unknown file type.")
        self.reader = csv.reader(self.f, *args, **kwargs)
        self.args = args
        self.kwargs = kwargs
        if skip:
            next(it.islice(self.reader, skip, None))
        if fieldnames:
            self.fieldnames = fieldnames
        else:
            skip += 1
            self.fieldnames = next(self.reader)
        # If the length is greater than max_num, stop eval and set length to max_num + 1
        self.length = sum(
            1
            for row in zip(self.reader, it.repeat(None, max_num + 1))
            if row != (([], None))
        )
        self.skip = skip
        # optimize sequential __getitem__ calls
        self.last_get_line = None
        self.line_cache = None

    def __iter__(self):
        self.seek_to_top()
        yield from map(self.pack_dict, it.islice(self.reader, self.skip, self.length))

    def __getitem__(self, i):
        if i < self.length:
            if self.last_get_line and i == self.last_get_line:
                return self.line_cache
            elif self.last_get_line and i == self.last_get_line + 1:
                d = self.pack_dict(next(self.reader))
            else:
                self.seek_to_top()
                d = self.pack_dict(next(it.islice(self.reader, i + self.skip, None)))
        else:
            raise IndexError
        self.last_get_line = i
        self.line_cache = d
        return d

    def __len__(self):
        return self.length

    def seek_to_top(self):
        self.last_get_line = None
        self.f.seek(0)
        self.reader = csv.reader(self.f, *self.args, **self.kwargs)

    def pack_dict(self, row):
        return dict(zip(self.fieldnames, row))
