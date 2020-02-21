from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from dashboard.forms import DataSourceForm, PriorityForm
from dashboard.models import DataSource, DataGroup, DataDocument
from django.db.models import Count, Q


@login_required()
def data_source_list(request, template_name="data_source/datasource_list.html"):
    datasources = DataSource.objects.all()
    ds_list, frm_list = [], []
    for ds in datasources:
        frm_list.append(PriorityForm(request.POST or None, instance=ds))
    registered = Count("datagroup__datadocument")
    uploaded = Count(
        "datagroup__datadocument", filter=~Q(datagroup__datadocument__file="")
    )
    extracted = Count("datagroup__datadocument__extractedtext")
    ds_list = DataSource.objects.annotate(registered=registered).annotate(
        uploaded=uploaded, extracted=extracted
    )
    out = zip(ds_list, frm_list)
    if request.method == "POST":
        datasource = DataSource.objects.get(pk=request.POST["ds_pk"])
        form = PriorityForm(request.POST or None, instance=datasource)
        if form.is_valid():
            priority = form.cleaned_data["priority"]
            datasource.priority = priority
            datasource.save()
            return redirect("data_source_list")
    return render(request, template_name, {"object_list": out})


@login_required()
def data_source_detail(request, pk, template_name="data_source/datasource_detail.html"):
    datasource = get_object_or_404(DataSource, pk=pk)
    docs = DataDocument.objects.filter(
        data_group__in=DataGroup.objects.filter(data_source=datasource)
    )
    datasource.registered = (len(docs) / float(datasource.estimated_records)) * 100
    datasource.uploaded = (
        len(docs.exclude(file="")) / float(datasource.estimated_records)
    ) * 100

    form = PriorityForm(request.POST or None, instance=datasource)
    if request.method == "POST":
        if form.is_valid():
            priority = form.cleaned_data["priority"]
            datasource.priority = priority
            datasource.save()
    datagroup_list = DataGroup.objects.filter(data_source=pk)
    context = {"object": datasource, "datagroup_list": datagroup_list, "form": form}
    return render(request, template_name, context)


@login_required()
def data_source_create(request, template_name=("data_source/" "datasource_form.html")):
    form = DataSourceForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("data_source_list")
    return render(request, template_name, {"form": form})


@login_required()
def data_source_update(
    request, pk, template_name=("data_source/" "datasource_form.html")
):
    datasource = get_object_or_404(DataSource, pk=pk)
    form = DataSourceForm(request.POST or None, instance=datasource)
    if form.is_valid():
        if form.has_changed():
            form.save()
        return redirect("data_source_detail", pk=pk)
    form.referer = request.META.get("HTTP_REFERER", None)
    return render(request, template_name, {"form": form})


@login_required()
def data_source_delete(
    request, pk, template_name=("data_source/" "datasource_confirm_delete.html")
):
    datasource = get_object_or_404(DataSource, pk=pk)
    if request.method == "POST":
        datasource.delete()
        return redirect("data_source_list")
    return render(request, template_name, {"object": datasource})
