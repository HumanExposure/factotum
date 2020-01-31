from django.db.models import Value, IntegerField
from django.shortcuts import render, get_object_or_404

from dashboard.models import DSSToxLookup, PUC, DataDocument


def chemical_detail(request, sid):
    chemical = get_object_or_404(DSSToxLookup, sid=sid)
    keysets = chemical.get_tag_sets()
    group_types = chemical.get_unique_datadocument_group_types_for_dropdown()
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
    context = {
        "chemical": chemical,
        "keysets": keysets,
        "group_types": group_types,
        "pucs": pucs,
        "show_filter": True,
    }
    return render(request, "chemicals/chemical_detail.html", context)
