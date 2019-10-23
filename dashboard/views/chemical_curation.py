import csv
import datetime

from django.contrib import messages
from django.db.models import Value, IntegerField
from django.shortcuts import render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.http import StreamingHttpResponse

from dashboard.models import RawChem, DSSToxLookup, DataGroup, DataDocument
from dashboard.forms import DataGroupSelector, ChemicalCurationFormSet
from dashboard.utils import get_extracted_models, gather_errors


@login_required()
def chemical_curation_index(request):
    template_name = "chemical_curation/chemical_curation_index.html"
    if "POST" == request.method:
        form_data = {
            "curate-TOTAL_FORMS": 0,
            "curate-INITIAL_FORMS": 0,
            "curate-MAX_NUM_FORMS": "",
        }
        formset = ChemicalCurationFormSet(form_data, request.FILES)
        if formset.is_valid():
            ups = formset.save()
            messages.success(request, f"{ups} records have been successfully uploaded.")
        else:
            errors = gather_errors(formset)
            for e in errors:
                messages.error(request, e)
    return render(request, template_name, {"dg_picker_form": DataGroupSelector()})


#
# Downloading uncurated raw chemical records by Data Group
#
# This clever way to combine writing the headers
# with writing the rows, including the "yield" keyword, is from
# https://stackoverflow.com/questions/45578196/adding-rows-manually-to-streaminghttpresponse-django


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def iterate_rawchems(rows, pseudo_buffer):
    writer = csv.writer(pseudo_buffer)
    yield pseudo_buffer.write("id,raw_cas,raw_chem_name,rid,datagroup_id\n")
    for row in rows:
        yield writer.writerow(
            [
                row["id"],
                row["raw_cas"],
                row["raw_chem_name"],
                row["rid"] if row["rid"] else "",
                row["dg_id"],
            ]
        )


@login_required()
def download_raw_chems_dg(request, pk):
    dg = DataGroup.objects.get(pk=pk)

    # Limit the response to 10,000 records
    uncurated_chems = (
        RawChem.objects.filter(dsstox_id=None)
        .filter(extracted_text__data_document__data_group=dg)
        .annotate(dg_id=Value(pk, IntegerField()))
        .values("id", "raw_cas", "raw_chem_name", "rid", "dg_id")[0:10000]
    )
    pseudo_buffer = Echo()
    response = StreamingHttpResponse(
        streaming_content=(iterate_rawchems(uncurated_chems, pseudo_buffer)),
        content_type="text/csv",
    )

    response["Content-Disposition"] = (
        'attachment; filename="uncurated_chemicals_%s_%s.csv"'
        % (pk, datetime.datetime.now().strftime("%Y%m%d"))
    )
    return response


@login_required()
def chemical_delete(request, doc_pk, chem_pk):
    doc = DataDocument.objects.get(pk=doc_pk)
    _, Chemical = get_extracted_models(doc.data_group.group_type.code)
    chem = Chemical.objects.get(pk=chem_pk)
    chem.delete()
    return redirect(doc)
