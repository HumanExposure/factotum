from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from dashboard.models import PUC
from django.db.models import Count


@login_required()
def puc_list(request, template_name="puc/puc_list.html"):
    pucs = PUC.objects.all().annotate(num_products=Count("products"))
    data = {}
    data["pucs"] = pucs
    return render(request, template_name, data)


@login_required()
def puc_detail(request, pk, template_name="puc/puc_detail.html"):
    puc = get_object_or_404(PUC, pk=pk)
    data = {}
    data["puc"] = puc
    data["linked_taxonomies"] = puc.get_linked_taxonomies()
    data["products"] = {}
    data["referer"] = (
        request.META["HTTP_REFERER"] if "HTTP_REFERER" in request.META else None
    )
    return render(request, template_name, data)
