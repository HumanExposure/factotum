from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import OuterRef, Subquery
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.db.models import Q

from dashboard.forms.forms import ExtractedHabitsAndPracticesForm
from dashboard.forms.tag_forms import ExtractedHabitsAndPracticesTagForm
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
    ExtractedLMDocForm,
)
from dashboard.models import (
    AuditLog,
    DataDocument,
    ExtractedListPresence,
    ExtractedText,
    FunctionalUse,
    Script,
    ExtractedListPresenceToTag,
    ExtractedListPresenceTag,
    ExtractedChemical,
    RawChem,
    AuditLog,
    ExtractedHabitsAndPractices,
    ExtractedHabitsAndPracticesTag,
    ExtractedHabitsAndPracticesToTag,
    ExtractedFunctionalUse,
)
from django.forms import inlineformset_factory

CHEMICAL_FORMS = {
    "CO": ExtractedChemicalForm,
    "LM": ExtractedChemicalForm,
    "FU": ExtractedFunctionalUseForm,
    "CP": ExtractedListPresenceForm,
    "HP": ExtractedHabitsAndPracticesForm,
    "HH": ExtractedHHRecForm,
}
CHEMICAL_TYPES = CHEMICAL_FORMS.keys()


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
    fufs = []
    tag_form = tag_form_url = None

    if doc.data_group.group_type.code in CHEMICAL_TYPES:
        if Child == ExtractedListPresence:
            tag_form = ExtractedListPresenceTagForm()
            tag_form_url = "save_list_presence_tag_form"

        if Child == ExtractedHabitsAndPractices:
            tag_form = ExtractedHabitsAndPracticesTagForm()
            tag_form_url = "save_habits_and_practices_tag_form"

        else:
            chem = (
                Child.objects.filter(extracted_text__data_document=doc)
                .prefetch_related("dsstox")
                .first()
            )
            FuncUseFormSet = inlineformset_factory(
                RawChem, FunctionalUse, fields=("report_funcuse",), extra=1
            )
            fufs = FuncUseFormSet(instance=chem)
    context = {
        "fufs": fufs,
        "doc": doc,
        "extracted_text": ext,
        "edit_text_form": ParentForm(instance=ext),  # empty form if ext is None
        "tag_form_url": tag_form_url,
        "tag_form": tag_form,
    }
    if doc.data_group.group_type.code == "CO":
        script_chem = (
            Child.objects.filter(extracted_text__data_document=doc)
            .filter(script__isnull=False)
            .first()
        )
        context["cleaning_script"] = script_chem.script if script_chem else None
    return render(request, template_name, context)


@method_decorator(login_required, name="dispatch")
class ChemCreateView(CreateView):
    template_name = "chemicals/chemical_add_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = DataDocument.objects.get(pk=self.kwargs.get("doc"))
        extra = 12 if doc.data_group.can_have_multiple_funcuse else 1
        FuncUseFormSet = inlineformset_factory(
            RawChem,
            FunctionalUse,
            fields=("report_funcuse",),
            extra=extra,
            can_delete=False,
        )
        context.update(
            {"formset": FuncUseFormSet, "doc": doc, "post_url": "chemical_create"}
        )
        if not "fufs" in context:
            context["fufs"] = FuncUseFormSet()
        return context

    def get_form_class(self):
        doc = DataDocument.objects.get(pk=self.kwargs.get("doc"))
        code = doc.data_group.group_type.code
        return CHEMICAL_FORMS[code]

    def form_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, fufs=formset))

    def form_valid(self, form):
        form.instance.extracted_text_id = self.kwargs.get("doc")
        self.object = form.save()
        FuncUseFormSet = self.get_context_data()["formset"]
        formset = FuncUseFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
            return render(
                self.request,
                "chemicals/chemical_create_success.html",
                {"chemical": self.object},
            )
        else:
            return self.form_invalid(form, formset)


@method_decorator(login_required, name="dispatch")
class ChemUpdateView(UpdateView):
    template_name = "chemicals/chemical_edit_form.html"
    model = RawChem

    def get_object(self, queryset=None):
        obj = super(ChemUpdateView, self).get_object(queryset=queryset)
        return RawChem.objects.get_subclass(pk=obj.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = self.object.extracted_text.data_document
        extra = 12 if doc.data_group.can_have_multiple_funcuse else 1
        FuncUseFormSet = inlineformset_factory(
            RawChem,
            FunctionalUse,
            fields=("report_funcuse",),
            extra=extra,
            can_delete=True,
        )
        context.update(
            {"formset": FuncUseFormSet, "doc": doc, "post_url": "chemical_update"}
        )
        if not "fufs" in context:
            context["fufs"] = FuncUseFormSet(instance=self.object)
        return context

    def get_form_class(self):
        code = self.object.extracted_text.group_type
        return CHEMICAL_FORMS[code]

    def form_invalid(self, form, formset):
        return self.render_to_response(self.get_context_data(form=form, fufs=formset))

    def form_valid(self, form):
        self.object = form.save()
        FuncUseFormSet = self.get_context_data()["formset"]
        formset = FuncUseFormSet(self.request.POST, instance=self.object)
        if formset.is_valid():
            formset.save()
            return render(
                self.request,
                "chemicals/chemical_create_success.html",
                {"chemical": self.object},
            )
        else:
            return self.form_invalid(form, formset)


@method_decorator(login_required, name="dispatch")
class EHPCreateView(CreateView):
    template_name = "chemicals/chemical_add_form.html"
    model = DataDocument
    form_class = ExtractedHabitsAndPracticesForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        doc = DataDocument.objects.get(pk=self.kwargs.get("doc"))
        context.update({"post_url": "ehp_create", "doc": doc})
        return context

    def form_valid(self, form):
        form.instance.extracted_text_id = self.kwargs.get("doc")
        extracted_habits_and_practices = form.save()
        return render(
            self.request,
            "chemicals/chemical_create_success.html",
            {"chemical": extracted_habits_and_practices},
        )


@method_decorator(login_required, name="dispatch")
class EHPUpdateView(UpdateView):
    template_name = "chemicals/chemical_edit_form.html"
    model = ExtractedHabitsAndPractices
    form_class = ExtractedHabitsAndPracticesForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"post_url": "ehp_update"})
        return context

    def form_valid(self, form):
        self.object = form.save()
        return render(
            self.request,
            "chemicals/chemical_create_success.html",
            {"chemical": self.object},
        )


@method_decorator(login_required, name="dispatch")
class EHPDeleteView(DeleteView):
    model = ExtractedHabitsAndPractices

    def get_success_url(self):
        return reverse("data_document", args=[self.kwargs.get("doc")])


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
def save_habits_and_practices_tag_form(request, pk):
    referer = request.POST.get("referer", "data_document")
    extracted_text = get_object_or_404(ExtractedText, pk=pk)
    tag_form = None
    values = request.POST.get("chems")
    chems = [int(chem) for chem in values.split(",")]
    selected = extracted_text.practices.filter(pk__in=chems)
    tags = ExtractedHabitsAndPracticesTag.objects.filter(
        pk__in=request.POST.getlist("tags")
    )
    for extracted_habits_and_practice in selected:
        tag_form = ExtractedHabitsAndPracticesTagForm(
            {"tags": tags}, instance=extracted_habits_and_practice
        )
        if tag_form.is_valid():
            tag_form.save()
        else:
            messages.error(request, tag_form.errors["tags"])
            break
    if not len(tag_form.errors):
        messages.success(
            request,
            f"Tags [{', '.join([str(tag) for tag in tag_form['tags'].data])}]"
            " are now connected to practices "
            f"[{', '.join([str(ehp) for ehp in selected])}]",
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
    form.referer = request.META.get("HTTP_REFERER", None)
    if form.is_valid():
        if form.has_changed():
            form.save()
        if request.POST.get("referer_page"):
            return redirect(request.POST.get("referer_page"))
        return redirect("data_document", pk=pk)

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
        return JsonResponse({"message": "success"})
    return JsonResponse(form.errors, status=400)


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


@login_required
def habits_and_practices_tag_delete(request, doc_pk, chem_pk, tag_pk):
    ExtractedHabitsAndPracticesToTag.objects.filter(
        content_object_id=chem_pk, tag_id=tag_pk
    ).delete()
    card = f"#chem-{chem_pk}"
    url = reverse("data_document", args=[doc_pk])
    url += card
    return redirect(url)


def chemical_audit_log(request, pk):
    chemical = RawChem.objects.filter(pk=pk).select_subclasses().first()
    fu_keys = FunctionalUse.objects.filter(chem_id=pk).values_list("id", flat=True)

    auditlog = AuditLog.objects.filter(
        Q(object_key=pk, model_name__in=[chemical._meta.model_name, "rawchem"])
        | Q(object_key__in=fu_keys, model_name__in=["functionaluse"])
    ).order_by("-date_created")

    return render(
        request,
        "chemicals/chemical_audit_log.html",
        {"chemical": chemical, "auditlog": auditlog},
    )


def chemical_cards(request, pk):
    doc = get_object_or_404(DataDocument, pk=pk)
    _, Child = get_extracted_models(doc.data_group.group_type.code)

    chemicals = Child.objects.filter(extracted_text__data_document=doc)

    if Child == ExtractedListPresence:
        chemicals = chemicals.prefetch_related("tags", "dsstox")
        template = "data_document/chemical_cards/co_cp_chemical_cards.html"

    elif Child == ExtractedChemical:
        chemicals = chemicals.order_by("component", "ingredient_rank").prefetch_related(
            "dsstox"
        )
        template = "data_document/chemical_cards/co_cp_chemical_cards.html"

    elif Child == ExtractedHabitsAndPractices:
        chemicals = chemicals.prefetch_related("tags")
        template = "data_document/chemical_cards/hp_cards.html"

    elif Child == ExtractedFunctionalUse:
        template = "data_document/chemical_cards/functional_use_chemical_cards.html"

    else:
        chemicals = chemicals.prefetch_related("dsstox")
        template = "data_document/chemical_cards/chemical_cards.html"

    return render(request, template, {"doc": doc, "chemicals": chemicals})
