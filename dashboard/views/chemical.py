import json
from collections import Counter, namedtuple

from django.contrib.auth.decorators import login_required
from django.db.models import Value, IntegerField
from django.shortcuts import render, get_object_or_404
from django.utils.safestring import SafeString
from django.http import JsonResponse

from dashboard.models import (
    DSSToxLookup,
    PUC,
    ExtractedListPresenceToTag,
    ExtractedListPresence,
    DataDocument,
)


def chemical_detail(request, sid):
    chemical = get_object_or_404(DSSToxLookup, sid=sid)
    keysets = chemical.get_tag_sets()
    pucs = PUC.objects.dtxsid_filter(sid).with_num_products().astree()
    # get parent PUCs too
    pucs.merge(
        PUC.objects.all()
        .annotate(num_products=Value(0, output_field=IntegerField()))
        .astree()
    )
    # Get cumulative product count
    for puc_name, puc_obj in pucs.items():
        puc_obj.cumnum_products = sum(
            p.num_products for p in pucs.objects[puc_name].values()
        )
    context = {"chemical": chemical, "keysets": keysets, "pucs": pucs}
    return render(request, "chemicals/chemical_detail.html", context)


def keywordset_documents(request, pk):
    ep = get_object_or_404(ExtractedListPresence, pk=pk)
    lp_querysets = []
    for tag_pk in ep.tags.values_list("pk", flat=True):
        ids = ExtractedListPresenceToTag.objects.filter(tag__id=tag_pk).values_list(
            "content_object", flat=True
        )
        lp_querysets.append(ExtractedListPresence.objects.filter(pk__in=ids))
    cleaned = ExtractedListPresence.objects.filter(pk__in=ids)
    # do an intersection of all chemicals w/ each tag
    for qs in lp_querysets:
        cleaned &= qs
    doc_ids = cleaned.values_list("extracted_text_id", flat=True)
    docs = DataDocument.objects.filter(pk__in=doc_ids)
    return JsonResponse({"data": list(docs.values("title", "id"))})
