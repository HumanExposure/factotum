from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, OuterRef
from django.shortcuts import render
from django.views import View

from dashboard.models import DataDocument, ProductDocument


class RawCategoryToPUC(LoginRequiredMixin, View):
    template_name = "product_curation/rawcategory/rawcategory_to_puc.html"

    def get(self, request):
        datadoc_by_raw_category = (
            DataDocument.objects.annotate(
                has_products=Exists(
                    ProductDocument.objects.filter(document=OuterRef("pk"))
                )
            )
            .filter(has_products=True)
            .values("data_group__name", "data_group__id", "raw_category")
            .annotate(document_count=Count("raw_category"))
            .filter(document_count__gte=50)
            .exclude(raw_category__isnull=False, raw_category="")
            .order_by("-document_count")
        )
        return render(
            request, self.template_name, context={"rows": list(datadoc_by_raw_category)}
        )
