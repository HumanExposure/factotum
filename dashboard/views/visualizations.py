from django.views import View

from dashboard.models import PUC, CumulativeProductsPerPuc
from django.db.models import Value, Case, When, IntegerField, F
from django.http import JsonResponse
from django.shortcuts import render


class Visualizations(View):
    """
    The basic GET version of the view
    """

    template_name = "visualizations/visualizations.html"

    def get(self, request):
        context = {}
        pucs = (
            CumulativeProductsPerPuc.objects.filter(puc__kind__code="FO")
            .filter(cumulative_product_count__gt=0)
            .astree()
        )
        context["formulation_pucs"] = pucs

        pucs = (
            CumulativeProductsPerPuc.objects.filter(puc__kind__code="AR")
            .filter(cumulative_product_count__gt=0)
            .astree()
        )
        context["article_pucs"] = pucs

        pucs = (
            CumulativeProductsPerPuc.objects.filter(puc__kind__code="OC")
            .filter(cumulative_product_count__gt=0)
            .astree()
        )
        context["occupation_pucs"] = pucs
        return render(request, self.template_name, context)


def bubble_PUCs(request):
    """This view is used to download all of the PUCs in nested JSON form.
    """
    dtxsid = request.GET.get("dtxsid", None)
    kind = request.GET.get("kind", "FO")
    if dtxsid:
        # filter by products by a related DSSTOX
        pucs = PUC.objects.dtxsid_filter(dtxsid)
        pucs = (
            pucs.filter(kind__code=kind)
            .with_num_products()
            .values("id", "gen_cat", "prod_fam", "prod_type", "num_products")
            .filter(num_products__gt=0)
            .annotate(level=level)
        )
        # convert the pucs to a simpletree
        pucs = pucs.values(
            "id", "gen_cat", "prod_fam", "prod_type", "num_products", "level"
        ).astree()
    else:
        if kind:
            pucs = CumulativeProductsPerPuc.objects.filter(puc__kind__code=kind).filter(
                cumulative_product_count__gt=0
            )
        else:
            pucs = CumulativeProductsPerPuc.objects.filter(
                cumulative_product_count__gt=0
            )

        pucs = (
            pucs.annotate(
                gen_cat=F("puc__gen_cat"),
                prod_fam=F("puc__prod_fam"),
                prod_type=F("puc__prod_type"),
            )  # change the nested __puc field names
            .values(
                "id",
                "gen_cat",
                "prod_fam",
                "prod_type",
                "product_count",
                "cumulative_product_count",
                "puc_level",
            )
            .flatdictastree()
        )


    return JsonResponse(pucs.asdict())


def collapsible_tree_PUCs(request):
    """This view is used to download all of the PUCs in nested JSON form.
    Regardless of if it is associated with an item
    """
    pucs = (
        PUC.objects.all()
        .filter(kind__code="FO")
        .values("id", "gen_cat", "prod_fam", "prod_type")
        .astree()
        .asdict()
    )

    # Name the first element.  Default = Root
    pucs["name"] = "Formulations"

    return JsonResponse(pucs)
