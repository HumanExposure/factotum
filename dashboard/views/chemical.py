from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.shortcuts import render, get_object_or_404
from django.utils.html import format_html
from django_datatables_view.base_datatable_view import BaseDatatableView
from cacheops import cache

from dashboard.models import (
    DSSToxLookup,
    PUC,
    ProductDocument,
    PUCKind,
    RawChem,
    DuplicateChemicals,
    CumulativeProductsPerPucAndSid,
)


def chemical_detail(request, sid, puc_id=None):
    chemical = get_object_or_404(DSSToxLookup, sid=sid)
    puc = get_object_or_404(PUC, id=puc_id) if puc_id else None
    keysets = chemical.get_tag_sets()
    group_types = chemical.get_unique_datadocument_group_types_for_dropdown()
    puc_kinds = PUCKind.objects.all()
    dss_pk = chemical.pk

    qs = CumulativeProductsPerPucAndSid.objects.filter(dsstoxlookup_id=dss_pk)

    formulation_pucs = qs.filter(puc__kind__code="FO").select_related("puc").astree()

    article_pucs = qs.filter(puc__kind__code="AR").select_related("puc").astree()

    occupation_pucs = qs.filter(puc__kind__code="OC").select_related("puc").astree()

    context = {
        "chemical": chemical,
        "keysets": keysets,
        "group_types": group_types,
        "formulation_pucs": formulation_pucs,
        "article_pucs": article_pucs,
        "occupation_pucs": occupation_pucs,
        "puc": puc,
        "show_filter": True,
        "puc_kinds": puc_kinds,
    }
    return render(request, "chemicals/chemical_detail.html", context)


@login_required()
def duplicate_chemical_records(
    request, template_name="chemicals/duplicate_chemicals.html"
):
    data = {"chemicals": {}}
    return render(request, template_name, data)


class DuplicateChemicalsJson(BaseDatatableView):
    model = RawChem
    columns = ["extracted_text__data_document__title", "dsstox__sid"]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = (
            DuplicateChemicals.objects.filter(
                extracted_text__data_document__data_group__group_type__code="CO"
            )
        ).values(
            "extracted_text__data_document",
            "extracted_text__data_document__title",
            "dsstox__sid",
        )
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)

        if column == "extracted_text__data_document__title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                "/datadocument/{}/".format(row["extracted_text__data_document"]),
                value,
            )
        return value


class ChemicalProductListJson(BaseDatatableView):
    model = ProductDocument
    columns = [
        "product.title",
        "document.title",
        "product.product_uber_puc.puc",
        "product.product_uber_puc.puc.kind.name",
    ]

    def get_filter_method(self):
        return self.FILTER_ICONTAINS

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        sid = self.request.GET.get("sid")
        if sid:
            return qs.filter(
                Q(document__extractedtext__rawchem__dsstox__sid=sid)
            ).distinct()
        return qs.filter()

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "product.title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.product.get_absolute_url(),
                value,
            )
        if column == "document.title":
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.document.get_absolute_url(),
                value,
            )
        if column == "product.product_uber_puc.puc":
            value = self._render_column(row, column)
            if value and hasattr(row, "get_absolute_url"):
                return format_html(
                    '<a href="{}" title="Go to PUC detail" target="_blank">{}</a>',
                    row.product.product_uber_puc.puc.get_absolute_url(),
                    value,
                )
        if column == "product.product_uber_puc.puc.kind.name":
            value = self._render_column(row, column)
            if value and hasattr(row, "get_absolute_url"):
                return format_html("<p>{}</p>", value)
        return value

    def ordering(self, qs):
        """ Get parameters from the request and prepare order by clause
        """

        # Number of columns that are used in sorting
        sorting_cols = 0
        if self.pre_camel_case_notation:
            try:
                sorting_cols = int(self._querydict.get("iSortingCols", 0))
            except ValueError:
                sorting_cols = 0
        else:
            sort_key = "order[{0}][column]".format(sorting_cols)
            while sort_key in self._querydict:
                sorting_cols += 1
                sort_key = "order[{0}][column]".format(sorting_cols)

        order = []
        order_columns = self.get_order_columns()

        for i in range(sorting_cols):
            # sorting column
            sort_dir = "asc"
            try:
                if self.pre_camel_case_notation:
                    sort_col = int(self._querydict.get("iSortCol_{0}".format(i)))
                    # sorting order
                    sort_dir = self._querydict.get("sSortDir_{0}".format(i))
                else:
                    sort_col = int(self._querydict.get("order[{0}][column]".format(i)))
                    # sorting order
                    sort_dir = self._querydict.get("order[{0}][dir]".format(i))
            except ValueError:
                sort_col = 0

            sdir = "-" if sort_dir == "desc" else ""
            sortcol = order_columns[sort_col]

            if isinstance(sortcol, list):
                for sc in sortcol:
                    order.append("{0}{1}".format(sdir, sc.replace(".", "__")))
            else:
                order.append("{0}{1}".format(sdir, sortcol.replace(".", "__")))

        if order:
            order_column = order[0]
            if order_column.endswith("product_uber_puc__puc"):
                # sort PUC data with nulls at bottom
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__gen_cat").desc(
                            nulls_last=True
                        ),
                        *order
                    )
                else:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__gen_cat").asc(
                            nulls_last=True
                        ),
                        *order
                    )
                return qs
            elif order_column.endswith("puc__kind__name"):
                # sort PUC data with nulls at bottom
                reverse_order = order_column.startswith("-")
                if reverse_order:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__kind__name").desc(
                            nulls_last=True
                        )
                    )
                else:
                    qs = qs.order_by(
                        F("product__product_uber_puc__puc__kind__name").asc(
                            nulls_last=True
                        )
                    )
            else:
                return qs.order_by(*order)
        return qs

    def filter_queryset(self, qs):
        puc = self.request.GET.get("category")
        s = self.request.GET.get("search[value]", None)
        puc_kind = self.request.GET.get("puc_kind")
        if puc:
            qs = qs.filter(Q(product__product_uber_puc__puc_id=puc))
        if s:
            qs = qs.filter(
                Q(product__title__icontains=s) | Q(document__title__icontains=s)
            ).distinct()
        if puc_kind and puc_kind != "all":
            if puc_kind == "none":
                qs = qs.filter(product__product_uber_puc__isnull=True)
            else:
                qs = qs.filter(product__product_uber_puc__puc__kind__code=puc_kind)
        return qs
