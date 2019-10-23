import csv
from djqscsv import render_to_csv_response
from django.db.models import CharField, Exists, F, OuterRef, Value as V
from django.db.models.functions import StrIndex, Substr
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.template.defaultfilters import pluralize

from dashboard.forms import DataGroupForm, create_detail_formset
from dashboard.forms.data_group import (
    BulkAssignProdForm,
    CleanCompFormSet,
    ExtractFileFormSet,
    UploadDocsForm,
    RegisterRecordsFormSet,
)
from dashboard.models import (
    ExtractedText,
    Script,
    ExtractedChemical,
    DataSource,
    DocumentType,
    GroupType,
    DataDocument,
    DataGroup,
)
from dashboard.utils import gather_errors
from factotum.settings import MEDIA_URL


@login_required()
def data_group_list(request, code=None, template_name="data_group/datagroup_list.html"):
    if code:
        group = get_object_or_404(GroupType, code=code)
        datagroup = DataGroup.objects.filter(group_type=group)
    else:
        datagroup = DataGroup.objects.all()
    data = {"object_list": datagroup}
    return render(request, template_name, data)


@login_required()
def data_group_detail(request, pk, template_name="data_group/datagroup_detail.html"):
    dg = get_object_or_404(DataGroup, pk=pk)
    tabledata = {
        "fsid": dg.fs_id,
        "boolComp": dg.is_composition,
        "boolHab": dg.is_habits_and_practices,
        "boolSD": dg.is_supplemental_doc,
        "numregistered": dg.registered_docs(),
        "nummatched": dg.matched_docs(),
        "numextracted": dg.extracted_docs(),
    }
    context = {
        "datagroup": dg,
        "tabledata": tabledata,
        "clean_comp_data_fieldnames": ", ".join(
            [
                "ExtractedChemical_id" if x == "id" else x
                for x in dg.get_clean_comp_data_fieldnames()
            ]
        ),
        "uploaddocs_form": None,
        "extfile_formset": None,
        "cleancomp_formset": None,
        "bulkassignprod_form": None,
    }
    # TODO: Lots of boilerplate code here.
    if dg.include_upload_docs_form():
        if "uploaddocs-submit" in request.POST:
            form = UploadDocsForm(dg, request.POST, request.FILES)
            context["uploaddocs_form"] = UploadDocsForm(dg, request.POST, request.FILES)
            if form.is_valid():
                num_saved = form.save()
                messages.success(
                    request,
                    "%d document%s uploaded successfully."
                    % (num_saved, pluralize(num_saved)),
                )
            else:
                errors = gather_errors(form)
                for e in errors:
                    messages.error(request, e)
        else:
            context["uploaddocs_form"] = UploadDocsForm(dg)

    if dg.include_extract_form():
        if "extfile-submit" in request.POST:
            formset = ExtractFileFormSet(dg, request.POST, request.FILES)
            context["extfile_formset"] = ExtractFileFormSet(dg, request.POST)
            if formset.is_valid():
                num_saved = formset.save()
                messages.success(
                    request,
                    "%d extracted record%s uploaded successfully."
                    % (num_saved, pluralize(num_saved)),
                )
            else:
                errors = gather_errors(formset)
                for e in errors:
                    messages.error(request, e)
        else:
            context["extfile_formset"] = ExtractFileFormSet(dg)

    if dg.include_clean_comp_data_form():
        if "cleancomp-submit" in request.POST:
            formset = CleanCompFormSet(dg, request.POST, request.FILES)
            context["cleancomp_formset"] = CleanCompFormSet(dg, request.POST)
            if formset.is_valid():
                num_saved = formset.save()
                messages.success(
                    request,
                    "%d clean composition data record%s uploaded successfully."
                    % (num_saved, pluralize(num_saved)),
                )
            else:
                errors = gather_errors(formset)
                for e in errors:
                    messages.error(request, e)
        else:
            context["cleancomp_formset"] = CleanCompFormSet(dg)

    if dg.include_bulk_assign_form():
        if "bulkassignprod-submit" in request.POST:
            form = BulkAssignProdForm(dg, request.POST, request.FILES)
            if form.is_valid():
                num_saved = form.save()
                messages.success(
                    request,
                    "%d product%s created successfully."
                    % (num_saved, pluralize(num_saved)),
                )
            else:
                errors = gather_errors(form)
                for e in errors:
                    messages.error(request, e)
        else:
            context["bulkassignprod_form"] = BulkAssignProdForm(dg)

    return render(request, template_name, context)


@login_required()
def data_group_documents_table(request, pk):
    dg = get_object_or_404(DataGroup, pk=pk)
    docs = (
        DataDocument.objects.filter(data_group=dg)
        .annotate(extracted=Exists(ExtractedText.objects.filter(pk=OuterRef("pk"))))
        .annotate(
            fileext=Substr(
                "filename", (StrIndex("filename", V("."))), output_field=CharField()
            )
        )
        .annotate(product_title=F("products__title"))
        .annotate(product_id=F("products__id"))
    )
    if dg.is_habits_and_practices:
        doc_vals = docs.values("id", "title", "matched", "fileext")
    elif dg.is_composition:
        doc_vals = docs.values(
            "id",
            "title",
            "matched",
            "fileext",
            "extracted",
            "product_id",
            "product_title",
        )
    elif dg.is_supplemental_doc:
        doc_vals = docs.values("id", "title", "matched", "fileext")
    else:
        doc_vals = docs.values("id", "title", "matched", "fileext", "extracted")
    return JsonResponse({"data": list(doc_vals)})


@login_required()
def data_group_create(request, pk, template_name="data_group/datagroup_form.html"):
    datasource = get_object_or_404(DataSource, pk=pk)
    group_key = DataGroup.objects.filter(data_source=datasource).count() + 1
    initial_values = {
        "downloaded_by": request.user,
        "name": f"{datasource} {group_key}",
        "data_source": datasource,
    }
    form = DataGroupForm(
        request.POST or None,
        request.FILES or None,
        user=request.user,
        initial=initial_values,
    )
    grouptypes = GroupType.objects.all()
    for grouptype in grouptypes:
        grouptype.codes = DocumentType.objects.compatible(grouptype)
    context = {"form": form, "datasource": datasource, "grouptypes": grouptypes}
    if request.method == "POST":
        if form.is_valid():
            datagroup = form.save()
            form_data = {
                "register-data_group": datagroup.pk,
                "register-TOTAL_FORMS": 0,
                "register-INITIAL_FORMS": 0,
                "register-MAX_NUM_FORMS": "",
            }
            csv_file = request.FILES["csv"].open()  # gets closed when saved above
            csv_dict = {"register-bulkformsetfileupload": csv_file}
            rf = RegisterRecordsFormSet(datagroup, form_data, csv_dict)
            if rf.is_valid():
                rf.save()
                return redirect("data_group_detail", pk=datagroup.id)
            else:
                if rf.non_form_errors():
                    for msg in rf.non_form_errors():
                        messages.error(request, msg)
                if not rf.non_form_errors() and rf.errors:
                    errors = gather_errors(rf)
                    for e in errors:
                        messages.error(request, e.strip("__all__:"))
                    # add more here, don't need to add more errors if any non_form_errors exist
                datagroup.delete()
                return render(request, template_name, context)
    return render(request, template_name, context)


@login_required()
def data_group_update(request, pk, template_name="data_group/datagroup_form.html"):
    datagroup = get_object_or_404(DataGroup, pk=pk)
    form = DataGroupForm(request.POST or None, instance=datagroup)
    if form.is_valid():
        if form.has_changed():
            form.save()
        return redirect("data_group_detail", pk=datagroup.id)
    form.referer = request.META.get("HTTP_REFERER", None)
    # updated 07/03/2019 - now none of the group types should be allowed to change (was ones with extracted docs only)
    form.fields["group_type"].disabled = True
    groups = GroupType.objects.all()
    for group in groups:
        group.codes = DocumentType.objects.compatible(group)
    return render(
        request,
        template_name,
        {"datagroup": datagroup, "form": form, "media": MEDIA_URL, "groups": groups},
    )


@login_required()
def data_group_delete(
    request, pk, template_name="data_source/datasource_confirm_delete.html"
):
    datagroup = get_object_or_404(DataGroup, pk=pk)
    if request.method == "POST":
        datagroup.delete()
        return redirect("data_group_list")
    return render(request, template_name, {"object": datagroup})


@login_required()
def habitsandpractices(request, pk, template_name="data_group/habitsandpractices.html"):
    doc = get_object_or_404(DataDocument, pk=pk)
    script = Script.objects.get(title="Manual (dummy)", script_type="EX")
    extext, created = ExtractedText.objects.get_or_create(
        data_document=doc, extraction_script=script
    )
    if created:
        extext.doc_date = "please add..."
    ExtractedTextForm, HPFormSet = create_detail_formset(doc)
    ext_form = ExtractedTextForm(request.POST or None, instance=extext)
    hp_formset = HPFormSet(request.POST or None, instance=extext, prefix="habits")
    context = {"doc": doc, "ext_form": ext_form, "hp_formset": hp_formset}
    if request.method == "POST" and "save" in request.POST:
        if hp_formset.is_valid():
            hp_formset.save()
        if ext_form.is_valid():
            ext_form.save()
        doc.save()
        context = {"doc": doc, "ext_form": ext_form, "hp_formset": hp_formset}
    return render(request, template_name, context)


@login_required
def download_raw_extracted_records(request, pk):
    datagroup = DataGroup.objects.get(pk=pk)
    et = ExtractedText.objects.filter(data_document__data_group=datagroup).first()
    columnlist = [
        "extracted_text_id",
        "id",
        "raw_cas",
        "raw_chem_name",
        "raw_min_comp",
        "raw_central_comp",
        "raw_max_comp",
        "unit_type__title",
    ]
    if et:
        qs = ExtractedChemical.objects.filter(
            extracted_text__data_document__data_group=datagroup
        ).values(*columnlist)
        return render_to_csv_response(
            qs,
            filename=(datagroup.get_name_as_slug() + "_raw_extracted_records.csv"),
            field_header_map={"id": "ExtractedChemical_id"},
            use_verbose_names=False,
        )
    else:
        qs = ExtractedChemical.objects.filter(
            extracted_text__data_document__id=pk
        ).values(*columnlist)
        return render_to_csv_response(
            qs, filename="raw_extracted_records.csv", use_verbose_names=False
        )


@login_required()
def download_unextracted_datadocuments(request, pk):
    datagroup = DataGroup.objects.get(pk=pk)
    documents = DataDocument.objects.filter(
        data_group=datagroup, matched=True, extractedtext__isnull=True
    ).values("pk", "filename")
    filename = datagroup.get_name_as_slug() + "_unextracted_documents.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=" + filename
    writer = csv.writer(response)
    writer.writerow(datagroup.get_extracted_template_fieldnames())
    for document in documents:
        writer.writerow([document["pk"], document["filename"]])
    return response


@login_required
def download_datadocuments(request, pk):
    datagroup = DataGroup.objects.get(pk=pk)
    documents = DataDocument.objects.filter(data_group=datagroup)
    filename = datagroup.get_name_as_slug() + "_documents.csv"
    return render_to_csv_response(documents, filename=filename, append_datestamp=True)


@login_required
def download_datadocument_zip_file(request, pk):
    datagroup = DataGroup.objects.get(pk=pk)
    zip_file_name = f"{datagroup.fs_id}.zip"
    zip_file = open(datagroup.get_zip_url(), "rb")
    response = HttpResponse(zip_file, content_type="application/zip")
    response["Content-Disposition"] = "attachment; filename=%s" % zip_file_name
    return response


@login_required
def download_registered_datadocuments(request, pk):
    datagroup = DataGroup.objects.filter(pk=pk).first()
    columnlist = ["filename", "title", "document_type", "url", "organization"]
    if datagroup:
        columnlist.insert(0, "id")
        filename = datagroup.get_name_as_slug() + "_registered_documents.csv"
        qs = DataDocument.objects.filter(data_group=datagroup).values(*columnlist)
        return render_to_csv_response(
            qs,
            filename=filename,
            field_header_map={"id": "DataDocument_id"},
            use_verbose_names=False,
            encoding="utf-8",
        )
    else:
        qs = DataDocument.objects.filter(data_group_id=0).values(*columnlist)
        return render_to_csv_response(
            qs, filename="registered_documents.csv", use_verbose_names=False
        )
