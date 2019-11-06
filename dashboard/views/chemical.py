from collections import Counter

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from dashboard.models import DSSToxLookup, PUC, ExtractedListPresence


def chemical_detail(request, sid):
    chemical = get_object_or_404(DSSToxLookup, sid=sid)
    qs = ExtractedListPresence.objects.filter(dsstox=chemical)
    tagDict = dict(Counter([tuple(x.tags.all()) for x in qs if x.tags.exists()]))
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
    context = {"chemical": chemical, "tagDict": tagDict, "pucs": pucs}
    return render(request, "chemicals/chemical_detail.html", context)
