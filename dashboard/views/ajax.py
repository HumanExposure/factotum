from django.http import JsonResponse
from dashboard.models import Product, DataDocument, DSSToxLookup, RawChem, GroupType
from dashboard.utils import GroupConcat
from django.db.models import Q, F
from django.views.decorators.cache import cache_page


def product_ajax(request):
    """ Returns a JSON response of products with the following optional arguments.

    Arguments:
        ``puc``
            limits return set to products matching this puc
        ``global_search``
            limits return set to products with titles matching search string
    """
    columns = ["title", "brand_name", "id"]
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    order_column = int(request.GET.get("order[0][column]", 0))
    order_direction = "-" if request.GET.get("order[0][dir]", "asc") == "desc" else ""
    order_column_name = columns[order_column]
    global_search = request.GET.get("search[value]", "")
    puc = request.GET.get("puc", "")
    if puc:
        all_objects = Product.objects.filter(Q(puc=puc))
    else:
        all_objects = Product.objects.all()
    total_count = all_objects.count()

    if global_search:
        all_objects = all_objects.filter(
            Q(title__icontains=global_search) | Q(brand_name__icontains=global_search)
        )
    filtered_count = all_objects.count()

    objects = []
    for i in all_objects.order_by(order_direction + order_column_name)[
        start : start + length
    ].values():
        ret = [i[j] for j in columns]
        objects.append(ret)

    return JsonResponse(
        {
            "recordsTotal": total_count,
            "recordsFiltered": filtered_count,
            "data": objects,
        }
    )


def document_ajax(request):
    """ Returns a JSON response of data documents with the following optional arguments.

    Arguments:
        ``puc``
            limits return set to products matching this puc
        ``global_search``
            limits return set to documents with titles matching search string
        ``sid``
            limits return set to documents associated with the curated chemical
            whose DTXSID is the search string
    """
    columns = ["title", "data_group__group_type__title", "id"]
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    order_column = int(request.GET.get("order[0][column]", 0))
    order_direction = "-" if request.GET.get("order[0][dir]", "asc") == "desc" else ""
    order_column_name = columns[order_column]
    global_search = request.GET.get("search[value]", "")
    puc = request.GET.get("puc", "")
    sid = request.GET.get("sid", "")
    if puc:
        all_objects = (
            DataDocument.objects.filter(Q(products__puc__id=puc))
            .select_related("data_group__group_type")
            .distinct()
        )
    elif sid:
        all_objects = (
            DataDocument.objects.filter(Q(extractedtext__rawchem__dsstox__sid=sid))
            .select_related("dsstox")
            .distinct()
        )
    else:
        all_objects = (
            DataDocument.objects.all()
            .select_related("data_group__group_type")
            .distinct()
        )
    total_count = all_objects.count()

    if global_search:
        all_objects = all_objects.filter(Q(title__icontains=global_search))
    filtered_count = all_objects.count()

    objects = []
    for i in all_objects.order_by(order_direction + order_column_name)[
        start : start + length
    ].values("title", "data_group_id", "id", "data_group__group_type__title"):
        ret = [i[j] for j in columns]
        objects.append(ret)

    return JsonResponse(
        {
            "recordsTotal": total_count,
            "recordsFiltered": filtered_count,
            "data": objects,
        }
    )


def chemical_ajax(request):
    """ Returns a JSON response of chemicals with the following optional arguments.

    Arguments:
        ``puc``
            limits return set to chemicals associated with this puc
        ``global_search``
            limits return set to chemicals matching the search string
    """
    columns = ["sid", "true_cas", "true_chemname"]
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    order_column = int(request.GET.get("order[0][column]", 0))
    order_direction = "-" if request.GET.get("order[0][dir]", "asc") == "desc" else ""
    order_column_name = columns[order_column]
    global_search = request.GET.get("search[value]", "")
    puc = request.GET.get("puc", "")
    if puc:
        all_objects = (
            RawChem.objects.filter(Q(extracted_text__data_document__products__puc=puc))
            .filter(dsstox__isnull=False)
            .select_related("dsstox")
            # .only("dsstox__sid", "dsstox__true_cas", "dsstox__true_chemname")
            .values(
                sid=F("dsstox__sid"),
                true_cas=F("dsstox__true_cas"),
                true_chemname=F("dsstox__true_chemname"),
            )
            .distinct()
        )
    else:
        all_objects = DSSToxLookup.objects.values("sid", "true_cas", "true_chemname")
    total_count = all_objects.count()

    if global_search:
        all_objects = all_objects.filter(
            Q(true_cas__icontains=global_search)
            | Q(true_chemname__icontains=global_search)
        )
    filtered_count = all_objects.count()

    objects = []
    for i in all_objects.order_by(order_direction + order_column_name)[
        start : start + length
    ].values("sid", "true_cas", "true_chemname"):
        ret = [i[j] for j in columns]
        objects.append(ret)

    return JsonResponse(
        {
            "recordsTotal": total_count,
            "recordsFiltered": filtered_count,
            "data": objects,
        }
    )


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
