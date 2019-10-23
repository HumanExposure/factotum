from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from dashboard.models import *


@login_required()
def extraction_script_list(request, template_name="qa/extraction_script_list.html"):
    """
    List view of extraction scripts
    """
    # TODO: the user is supposed to be able to click the filter button at the top of the table
    # and toggle between seeing all scripts and seeing only the ones with incomplete QA
    extractionscripts = Script.objects.filter(script_type="EX")
    data = {}
    data["object_list"] = extractionscripts
    return render(request, template_name, data)


@login_required()
def extraction_script_detail(
    request, pk, template_name="extraction_script/extraction_script_detail.html"
):
    extractionscript = get_object_or_404(Script, pk=pk)
    data = {}
    data["object_list"] = extractionscript
    return render(request, template_name, data)


@login_required()
def extraction_script_delete_list(
    request, template_name="extraction_script/delete.html"
):
    """
    List view of extraction scripts for deleting all the extractedtext objects
    in one of them
    """
    extractionscripts = Script.objects.filter(script_type="EX").annotate(
        num_ex=Count("extractedtext")
    )
    data = {}
    data["object_list"] = extractionscripts
    return render(request, template_name, data)
