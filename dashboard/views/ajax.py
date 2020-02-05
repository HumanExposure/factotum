from django_datatables_view.base_datatable_view import BaseDatatableView
from django.http import JsonResponse
from django.db.models import Q
from django.utils.html import format_html
from django.views.decorators.cache import cache_page
from django.template.defaultfilters import truncatechars

from dashboard.utils import GroupConcat
from dashboard.models import (
    Product,
    GroupType,
    DataDocument,
    DSSToxLookup,
    RawChem,
    ExtractedListPresence,
    ExtractedListPresenceToTag,
)


class FilterDatatableView(BaseDatatableView):
    def get_filter_method(self):
        return self.FILTER_ICONTAINS


class ProductListJson(FilterDatatableView):
    model = Product
    columns = ["title", "brand_name"]

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if column == "title":
            return format_html(
                '<a href="{}" title="Go to Product detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        if puc:
            return qs.filter(Q(puc=puc))
        return qs


class DocumentListJson(FilterDatatableView):
    model = DataDocument
    columns = ["title", "data_group.group_type.title"]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        sid = self.request.GET.get("sid")
        if puc:
            return qs.filter(Q(products__puc=puc)).distinct()
        if sid:
            return qs.filter(Q(extractedtext__rawchem__dsstox__sid=sid)).distinct()
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        chem = self.request.GET.get("chem_detail")
        if column == "title":
            if chem:
                value = truncatechars(value, 50)
            return format_html(
                '<a href="{}" title="Go to Document detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def filter_queryset(self, qs):
        qs = super().filter_queryset(qs)
        puc = self.request.GET.get("category")
        pid = self.request.GET.get("pid")
        group_type = self.request.GET.get("group_type")
        if puc:
            qs = qs.filter(Q(products__puc=puc))
        if group_type:
            if group_type == "-1":
                return qs
            qs = qs.filter(data_group__group_type__id=group_type)
        if pid:
            ep = ExtractedListPresence.objects.get(pk=pid)
            lp_querysets = []
            for tag_pk in ep.tags.values_list("pk", flat=True):
                ids = ExtractedListPresenceToTag.objects.filter(
                    tag__id=tag_pk
                ).values_list("content_object", flat=True)
                lp_querysets.append(ExtractedListPresence.objects.filter(pk__in=ids))
            cleaned = ExtractedListPresence.objects.filter(pk__in=ids)
            # do an intersection of all chemicals w/ each tag
            for lp_qs in lp_querysets:
                cleaned &= lp_qs
            doc_ids = cleaned.values_list("extracted_text_id", flat=True)
            qs = qs.filter(pk__in=doc_ids)
        return qs


class ChemicalListJson(FilterDatatableView):
    model = DSSToxLookup
    columns = ["sid", "true_cas", "true_chemname"]

    def get_initial_queryset(self):
        qs = super().get_initial_queryset()
        puc = self.request.GET.get("puc")
        if puc:
            vals = (
                RawChem.objects.filter(dsstox__isnull=False)
                .filter(Q(extracted_text__data_document__products__puc=puc))
                .values("dsstox")
            )
            return qs.filter(pk__in=vals)
        return qs

    def render_column(self, row, column):
        value = self._render_column(row, column)
        if value and hasattr(row, "get_absolute_url"):
            if column == "true_chemname":
                return format_html(truncatechars(value, 89))
            return format_html(
                '<a href="{}" title="Go to Chemical detail" target="_blank">{}</a>',
                row.get_absolute_url(),
                value,
            )
        return value

    def filter_queryset(self, qs):
        s = self.request.GET.get("search[value]", None)
        if s:
            qs = qs.filter(
                Q(true_cas__icontains=s) | Q(true_chemname__icontains=s)
            ).distinct()
        return qs


@cache_page(86400)
def sids_by_grouptype_ajax(request):
    """Counts the number of DTXSIDs per GroupType. Multiple
    GroupTypes can be associated with a single DTXSID. The
    GroupType set is also counted.
    The output is a JSON to be rendered with this library
    https://github.com/benfred/venn.js
    Args:
        request ([type]): [description]
    """
    qs = DSSToxLookup.objects.annotate(
        grouptype=GroupConcat(
            "curated_chemical__extracted_text__data_document__data_group__group_type__id",
            distinct=True,
        )
    ).values_list("grouptype", flat=True)
    sets_cnt = {}

    def add_set(key):
        # Adds or creates set to sets_dict
        if key not in sets_cnt:
            sets_cnt[key] = 1
        else:
            sets_cnt[key] += 1

    # Count sets
    for group_str in qs:
        # Ignore "None"
        if group_str:
            # Each value is a concatenation of GroupType IDs separated by a comma.
            # Lets split them
            groups = group_str.split(",")
            # Then turn them into a list of integers
            groups = [int(i) for i in groups]
            # We want to make sure they are consistently sorted
            groups.sort()
            # We make them a tuple to use as a dictionary key
            groups = tuple(groups)
            # Record a count on it
            add_set(groups)
            # If this is more than one GroupType, we also want to count the GroupTypes
            # within the set
            if len(groups) > 1:
                for group in groups:
                    add_set((group,))

    # Here is a dictionary relating the GroupType ID we've counted on to its title
    titles = {
        g["id"]: g["title"]
        for g in GroupType.objects.all().order_by("id").values("id", "title")
    }
    # Create data
    sets = []
    for set_ids, set_cnt in sets_cnt.items():
        # List the titles, not IDs
        set_groups = [titles[i] for i in set_ids]
        # Make the final dictionary output
        sets.append({"sets": set_groups, "size": set_cnt})

    return JsonResponse({"data": sets})
