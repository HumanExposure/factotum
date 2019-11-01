from django.http import JsonResponse
from dashboard.models import Product
from django.db.models import Q


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
