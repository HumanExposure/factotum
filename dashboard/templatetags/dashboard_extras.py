import os
from django import template

register = template.Library()
from django.template.defaultfilters import register


ICON_MAP = {
    ".csv": "-csv",
    ".pdf": "-pdf",
    ".txt": "-alt",
    ".doc": "-word",
    ".docx": "-word",
    ".xls": "-excel",
    ".xlsx": "-excel",
    ".jpg": "-image",
    ".tiff": "-image",
}


@register.filter
def fileicon(value):
    _, ext = os.path.splitext(value)
    return "fa-file" + ICON_MAP.get(ext.lower(), "")


@register.filter(name="dict_key")
def dict_key(d, k):
    """Returns the given key from a dictionary."""
    return d.get(k)
