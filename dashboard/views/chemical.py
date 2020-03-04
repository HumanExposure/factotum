from django.db.models import Value, IntegerField, Q
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from django_datatables_view.base_datatable_view import BaseDatatableView

from dashboard.models import DSSToxLookup, PUC, ProductDocument


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


class ChemicalProductListJson(BaseDatatableView):
    model = ProductDocument
    columns = ["product", "document", "product.uber_puc"]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        sid = self.request.GET.get("sid")
        if sid:
            return qs.filter(Q(document__extractedtext__rawchem__dsstox__sid=sid)).distinct()
        return qs.filter()

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "product":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.product.get_absolute_url(),
                value,
            )
        if column == "document":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.document.get_absolute_url(),
                value,
            )
        if column == "product.uber_puc":
            value = self._render_column(row, column)
            if value and hasattr(row, "get_absolute_url"):
                return format_html(
                    '<a href="{}" title="Go to PUC detail" target="_blank">{}</a>',
                    row.product.uber_puc.get_absolute_url(),
                    value,
                )
        return value

    def filter_queryset(self, qs):
        puc = self.request.GET.get("category")
        s = self.request.GET.get("search[value]", None)
        if puc:
            qs = qs.filter(Q(product__puc=puc)).distinct()
        if s:
            qs = qs.filter(
                Q(product__title__icontains=s) | Q(document__title__icontains=s)
            ).distinct()
        return qs
