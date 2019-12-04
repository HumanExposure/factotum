import json
from collections import Counter, namedtuple

from django.contrib.auth.decorators import login_required
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
    qs = ExtractedListPresence.objects.filter(dsstox=chemical)
    tagsets, presence_ids = [], []
    for x in qs:
        if x.tags.exists():
            tagsets.append(tuple(x.tags.all()))
            presence_ids.append(x.pk)
    one = {}
    for i, j in enumerate(tagsets):
        one[hash(j)] = presence_ids[i]
    counter = Counter(tagsets)
    KeywordSet = namedtuple("KeywordSet", "keywords count presence_id")
    keysets = []
    for kw_set, count in counter.items():
        kw_hash = hash(kw_set)
        if one[kw_hash]:
            keysets.append(
                KeywordSet(keywords=kw_set, count=count, presence_id=one[kw_hash])
            )
    pucs = PUC.objects.dtxsid_filter(sid).with_num_products().astree()
    # get parent PUCs too
    parent_pucs = {}
    for puc in PUC.objects.all():
        names = tuple(n for n in (puc.gen_cat, puc.prod_fam, puc.prod_type) if n)
        parent_pucs[names] = puc
    for leaf in pucs.children:
        if not leaf.value:
            leaf.value = parent_pucs[(leaf.name,)]
        for leaflet in leaf.children:
            if not leaflet.value:
                leaflet.value = parent_pucs[(leaf.name, leaflet.name)]
            for needle in leaflet.children:
                if not needle.value:
                    needle.value = parent_pucs[(leaf.name, leaflet.name, needle.name)]
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
