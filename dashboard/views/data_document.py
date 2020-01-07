from django.contrib import messages
from django.http import HttpResponse
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView
from django.shortcuts import render, redirect, get_object_or_404, reverse

from dashboard.utils import get_extracted_models
from dashboard.forms import (
    ExtractedListPresenceTagForm,
    create_detail_formset,
    DataDocumentForm,
    DocumentTypeForm,
    ExtractedChemicalForm,
    ExtractedFunctionalUseForm,
    ExtractedHHRecForm,
    ExtractedListPresenceForm,
)
from dashboard.models import (
    AuditLog,
    DataDocument,
    ExtractedListPresence,
    ExtractedText,
    Script,
    ExtractedListPresenceToTag,
    ExtractedListPresenceTag,
    ExtractedChemical,
    RawChem,
    AuditLog,
)


def data_document_detail(request, pk):
    template_name = "data_document/data_document_detail.html"
    doc = get_object_or_404(DataDocument, pk=pk)
    if doc.data_group.group_type.code == "SD":
        messages.info(
            request,
            f'"{doc}" has no detail page. GroupType is "{doc.data_group.group_type}"',
        )
        return redirect(reverse("data_group_detail", args=[doc.data_group_id]))
    ParentForm, _ = create_detail_formset(doc)
    Parent, Child = get_extracted_models(doc.data_group.group_type.code)
    ext = Parent.objects.filter(pk=doc.pk).first()
    chemicals = Child.objects.filter(
        extracted_text__data_document=doc
    ).prefetch_related("dsstox")
    if Child == ExtractedListPresence:
        chemicals = chemicals.prefetch_related("tags")
    lp = ExtractedListPresence.objects.filter(
        extracted_text=ext if ext else None
    ).first()
    tag_form = ExtractedListPresenceTagForm()
    context = {
        "doc": doc,
        "extracted_text": ext,
        "chemicals": chemicals,
        "edit_text_form": ParentForm(instance=ext),  # empty form if ext is None
        "list_presence_tag_form": tag_form if lp else None,
    }
    if doc.data_group.group_type.code == "CO":
        script_chem = chemicals.filter(script__isnull=False).first()
        context["cleaning_script"] = script_chem.script if script_chem else None
    return render(request, template_name, context)


@method_decorator(login_required, name="dispatch")
class ChemCreateView(CreateView):
    template_name = "chemicals/chemical_add_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["doc"] = DataDocument.objects.get(pk=self.kwargs.get("doc"))
        return context

    def get_form_class(self):
        doc = DataDocument.objects.get(pk=self.kwargs.get("doc"))
        code = doc.data_group.group_type.code
        if code == "CO":
            return ExtractedChemicalForm
        if code == "FU":
            return ExtractedFunctionalUseForm
        if code == "CP":
            return ExtractedListPresenceForm
        if code == "HH":
            return ExtractedHHRecForm

    def form_valid(self, form):
        form.instance.extracted_text_id = self.kwargs.get("doc")
        self.object = form.save()
        return render(
            self.request,
            "chemicals/chemical_create_success.html",
            {"chemical": self.object},
        )


@method_decorator(login_required, name="dispatch")
class ChemUpdateView(UpdateView):
    template_name = "chemicals/chemical_edit_form.html"
    model = RawChem

    def get_object(self, queryset=None):
        obj = super(ChemUpdateView, self).get_object(queryset=queryset)
        return RawChem.objects.get_subclass(pk=obj.pk)

    def get_form_class(self):
        code = self.object.extracted_text.group_type
        if code == "CO":
            return ExtractedChemicalForm
        if code == "CP":
            return ExtractedListPresenceForm
        if code == "HH":
            return ExtractedHHRecForm

    def form_valid(self, form):
        self.object = form.save()

        return render(
            self.request,
            "chemicals/chemical_create_success.html",
            {"chemical": self.object},
        )


@login_required()
def save_doc_form(request, pk):
    """Writes changes to the data document form

    The request object should have a 'referer' key to redirect the
    browser to the appropriate place after saving the edits

    Invoked by changing the document type in the data document detail view or the
    extracted text QA page template
    """

    referer = request.POST.get("referer", "data_document")
    doc = get_object_or_404(DataDocument, pk=pk)
    document_type_form = DocumentTypeForm(request.POST, instance=doc)
    if document_type_form.is_valid() and document_type_form.has_changed():
        document_type_form.save()
    return redirect(referer, pk=pk)


@login_required()
def data_document_note(request, pk):
    doc = get_object_or_404(DataDocument, pk=pk)
    doc_note = request.POST["dd_note"]
    doc.note = doc_note
    doc.save()
    return redirect("data_document", pk=pk)


@login_required()
def save_ext_form(request, pk):
    referer = request.POST.get("referer", "data_document")
    doc = get_object_or_404(DataDocument, pk=pk)
    ExtractedTextForm, _ = create_detail_formset(doc)
    extracted_text = ExtractedText.objects.get_subclass(pk=pk)
    ext_text_form = ExtractedTextForm(request.POST, instance=extracted_text)
    if ext_text_form.is_valid() and ext_text_form.has_changed():
        ext_text_form.save()
    return redirect(referer, pk=pk)


@login_required()
def save_list_presence_tag_form(request, pk):
    referer = request.POST.get("referer", "data_document")
    extracted_text = get_object_or_404(ExtractedText, pk=pk)
    tag_form = None
    values = request.POST.get("chems")
    chems = [int(chem) for chem in values.split(",")]
    selected = extracted_text.rawchem.filter(pk__in=chems).select_subclasses()
    for extracted_list_presence in selected:
        tag_form = ExtractedListPresenceTagForm(
            request.POST or None, instance=extracted_list_presence
        )
        if tag_form.is_valid():
            tag_form.save()
        else:
            messages.error(request, tag_form.errors["tags"])
            break
    if not len(tag_form.errors):
        messages.success(
            request,
            "The following keywords are now associated with these list presence objects: %s"
            % tag_form["tags"].data,
        )
    return redirect(referer, pk=pk)


@login_required()
def data_document_delete(request, pk):
    doc = get_object_or_404(DataDocument, pk=pk)
    datagroup_id = doc.data_group_id
    if request.method == "POST":
        doc.delete()
        return redirect("data_group_detail", pk=datagroup_id)
    return render(
        request, "data_source/datasource_confirm_delete.html", {"object": doc}
    )


@login_required
def data_document_edit(request, pk):
    datadocument = get_object_or_404(DataDocument, pk=pk)
    form = DataDocumentForm(request.POST or None, instance=datadocument)
    if form.is_valid():
        if form.has_changed():
            form.save()
        return redirect("data_document", pk=pk)
    form.referer = request.META.get("HTTP_REFERER", None)
    return render(request, "data_document/data_document_form.html", {"form": form})


@login_required
def extracted_text_edit(request, pk):
    doc = get_object_or_404(DataDocument, pk=pk)
    ParentForm, _ = create_detail_formset(doc, extra=0, can_delete=False)
    model = ParentForm.Meta.model
    script = Script.objects.get(title__icontains="Manual (dummy)", script_type="EX")
    try:
        extracted_text = model.objects.get_subclass(data_document_id=pk)
    except ExtractedText.DoesNotExist:
        extracted_text = model(data_document_id=pk, extraction_script=script)
    form = ParentForm(request.POST, instance=extracted_text)
    if form.is_valid():
        form.save()
        doc.save()
        return redirect("data_document", pk=doc.pk)
    else:
        extracted_text.delete()
        return HttpResponse("Houston, we have a problem.")


@login_required
def list_presence_tag_curation(request):
    documents = (
        DataDocument.objects.filter(
            data_group__group_type__code="CP", extractedtext__rawchem__isnull=False
        )
        .distinct()
        .exclude(
            extractedtext__rawchem__in=ExtractedListPresenceToTag.objects.values(
                "content_object_id"
            )
        )
    )
    return render(
        request, "data_document/list_presence_tag.html", {"documents": documents}
    )


@login_required
def list_presence_tag_delete(request, doc_pk, chem_pk, tag_pk):
    elp = ExtractedListPresence.objects.get(pk=chem_pk)
    tag = ExtractedListPresenceTag.objects.get(pk=tag_pk)
    ExtractedListPresenceToTag.objects.get(content_object=elp, tag=tag).delete()
    card = f"#chem-{chem_pk}"
    url = reverse("data_document", args=[doc_pk])
    url += card
    return redirect(url)


def chemical_audit_log(request, pk):
    chemical = RawChem.objects.filter(pk=pk).select_subclasses().first()
    auditlog = AuditLog.objects.filter(
        object_key=pk,
        model_name__in=[chemical.auditlog_model_name, "rawchem"],
    ).order_by("-date_created")
    return render(
        request,
        "chemicals/chemical_audit_log.html",
        {"chemical": chemical, "auditlog": auditlog},
    )
