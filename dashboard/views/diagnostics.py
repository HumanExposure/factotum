import os
from django.core.management.base import BaseCommand, CommandError
from dashboard.models import *
from django.conf import settings
from pathlib import Path, PurePath
from django.shortcuts import render

# from djqscsv import render_to_csv_response
from django.contrib.auth.decorators import login_required


@login_required()
def data_group_diagnostics(request, pk=None):
    if pk == None:
        dgs = DataGroup.objects.all()
    else:
        dgs = DataGroup.objects.filter(pk=pk)

    dgs = dgs.values()
    for dg in dgs:
        dgmod = DataGroup.objects.get(pk=dg["id"])
        dg["get_zip_url"] = dgmod.get_zip_url()
        dg["get_dg_folder"] = dgmod.get_dg_folder()
        dg["csv_name"] = dgmod.csv.name
        dg["csv_url"] = dgmod.csv_url
        dg["csv"] = dgmod.csv
        dg["get_dg_folder"] = dgmod.get_dg_folder()
        dg["get_name_as_slug"] = dgmod.get_name_as_slug()
        dg["fs_id"] = dgmod.fs_id
        dg["dg_folder"] = dgmod.dg_folder

    context = {"datagroups": dgs}
    template_name = "data_group/datagroup_diagnostics.html"
    return render(request, template_name, context)
