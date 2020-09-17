import csv
import datetime

from dateutil.relativedelta import relativedelta
from django.db.models import Count, DateField, DateTimeField, F, Q
from django.db.models.functions import Trunc
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from dashboard.models import (
    PUC,
    DataDocument,
    ExtractedListPresenceTag,
    Product,
    ProductToPUC,
    RawChem,
    GroupType,
    FunctionalUseCategory,
)


def index(request):
    stats = {}
    stats["datadocument_count"] = DataDocument.objects.count()
    stats["product_count"] = Product.objects.count()
    stats["chemical_count"] = RawChem.objects.count()
    stats["product_with_puc_count"] = (
        ProductToPUC.objects.values("product_id").distinct().count()
    )
    stats["curated_chemical_count"] = RawChem.objects.filter(
        dsstox__isnull=False
    ).count()
    stats["dsstox_sid_count"] = RawChem.objects.values("dsstox__sid").distinct().count()

    pucs = (
        PUC.objects.with_num_products()
        .filter(kind__code="FO")
        .filter(cumulative_products__gt=0)
        .astree()
    )
    stats["formulation_pucs"] = pucs

    pucs = (
        PUC.objects.with_num_products()
        .filter(kind__code="AR")
        .filter(cumulative_products__gt=0)
        .astree()
    )
    stats["article_pucs"] = pucs

    return render(request, "dashboard/index.html", stats)


def datadocument_count_by_date():
    # Datasets to populate linechart with document-upload statistics
    # Number of datadocuments, both overall and by type, that have been uploaded
    # as of each date
    current_date = datetime.datetime.strftime(datetime.datetime.now(), "%Y-%m-%d")
    select_upload_date = {"upload_date": """date(dashboard_datadocument.created_at)"""}
    document_stats = {}
    document_stats["all"] = list(
        DataDocument.objects.extra(select=select_upload_date)
        .values("upload_date")
        .annotate(document_count=Count("id"))
        .order_by("upload_date")
    )
    document_stats_by_type = (
        DataDocument.objects.extra(select=select_upload_date)
        .values("upload_date")
        .annotate(source_type=F("document_type__title"), document_count=Count("id"))
        .order_by("upload_date")
    )
    document_stats["product"] = list(
        document_stats_by_type.filter(source_type="product")
    )
    document_stats["msds_sds"] = list(
        document_stats_by_type.filter(source_type="msds/sds")
    )
    for type in {"all"}:
        document_count = 0
        for item in document_stats[type]:
            if isinstance(item["upload_date"], datetime.date):
                item["upload_date"] = datetime.date.strftime(
                    (item["upload_date"]), "%Y-%m-%d"
                )
            document_count += item["document_count"]
            item["document_count"] = document_count
        # if final record isn't for current date, create one
        for item in document_stats[type][len(document_stats[type]) - 1 :]:
            if item["upload_date"] != current_date:
                document_stats[type].append(
                    {"upload_date": current_date, "document_count": document_count}
                )
    return document_stats


def datadocument_count_by_month():
    # GROUP BY issue solved with https://stackoverflow.com/questions/8746014/django-group-by-date-day-month-year
    chart_start_datetime = datetime.datetime(
        datetime.datetime.now().year - 1, min(12, datetime.datetime.now().month + 1), 1
    )
    document_stats = list(
        DataDocument.objects.filter(created_at__gte=chart_start_datetime)
        .annotate(
            upload_month=(Trunc("created_at", "month", output_field=DateTimeField()))
        )
        .values("upload_month")
        .annotate(document_count=(Count("id")))
        .values("document_count", "upload_month")
        .order_by("upload_month")
    )
    if len(document_stats) < 12:
        for i in range(0, 12):
            chart_month = chart_start_datetime + relativedelta(months=i)
            if (
                i + 1 > len(document_stats)
                or document_stats[i]["upload_month"] != chart_month
            ):
                document_stats.insert(
                    i, {"document_count": "0", "upload_month": chart_month}
                )
    return document_stats


def product_with_puc_count_by_month():
    # GROUP BY issue solved with https://stackoverflow.com/questions/8746014/django-group-by-date-day-month-year
    chart_start_datetime = datetime.datetime(
        datetime.datetime.now().year - 1, min(12, datetime.datetime.now().month + 1), 1
    )
    product_stats = list(
        ProductToPUC.objects.filter(created_at__gte=chart_start_datetime)
        .annotate(
            puc_assigned_month=(Trunc("created_at", "month", output_field=DateField()))
        )
        .values("puc_assigned_month")
        .annotate(product_count=Count("product", distinct=True))
        .order_by("puc_assigned_month")
    )

    if len(product_stats) < 12:
        for i in range(0, 12):
            chart_month = chart_start_datetime + relativedelta(months=i)
            if (
                i + 1 > len(product_stats)
                or product_stats[i]["puc_assigned_month"] != chart_month
            ):
                product_stats.insert(
                    i, {"product_count": "0", "puc_assigned_month": chart_month}
                )
    return product_stats


def grouptype_stats(request):
    """Return a json representation of the stats for GroupType.
    Returns:
    json: { "data" : [[ title, documentcount (%), rawchemcount (%), curatedchemcount (%) ], [...], ], }
    """
    grouptype_rows = GroupType.objects.annotate(
        documentcount=Count("datagroup__datadocument", distinct=True),
        rawchemcount=Count(
            "datagroup__datadocument__extractedtext__rawchem", distinct=True
        ),
        curatedchemcount=Count(
            "datagroup__datadocument__extractedtext__rawchem",
            distinct=True,
            filter=Q(
                datagroup__datadocument__extractedtext__rawchem__dsstox_id__isnull=False
            ),
        ),
    ).order_by("-documentcount")

    datadocument_total = rawchem_total = curatedchem_total = 0
    for row in grouptype_rows:
        datadocument_total += row.documentcount
        rawchem_total += row.rawchemcount
        curatedchem_total += row.curatedchemcount

    return JsonResponse(
        {
            "data": [
                [
                    row.title,
                    # Document count by grouptype with % total
                    f"{row.documentcount} ({(row.documentcount / (datadocument_total or 1))*100:.0f}%)",
                    # Raw chemical counts by grouptype with % total
                    f"{row.rawchemcount} ({(row.rawchemcount / (rawchem_total or 1))*100:.0f}%)",
                    # Curated chemical counts by grouptypes with % total
                    f"{row.curatedchemcount} ({(row.curatedchemcount / (curatedchem_total or 1))*100:.0f}%)",
                ]
                for row in grouptype_rows
            ]
        }
    )


def download_PUCs(request):
    """This view is used to download all of the PUCs in CSV form.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="PUCs.csv"'
    pucs = (
        PUC.objects.order_by("gen_cat", "prod_fam", "prod_type")
        .with_allowed_attributes()
        .with_assumed_attributes()
        .with_num_products()
        .astree()
    )
    writer = csv.writer(response)
    cols = [
        "General category",
        "Product family",
        "Product type",
        "Allowed attributes",
        "Assumed attributes",
        "Description",
        "PUC type",
        "PUC level",
        "Product count",
        "Cumulative product count",
    ]
    writer.writerow(cols)
    for puc_key, puc in pucs.items():
        row = [
            puc.gen_cat,
            puc.prod_fam,
            puc.prod_type,
            puc.allowed_attributes,
            puc.assumed_attributes,
            puc.description,
            puc.kind,
            len(puc_key),
            puc.num_products,
            sum(p.num_products for p in pucs.objects[puc_key].values()),
        ]
        writer.writerow(row)
    return response


def bubble_PUCs(request):
    """This view is used to download all of the PUCs in nested JSON form.
    """
    dtxsid = request.GET.get("dtxsid", None)
    kind = request.GET.get("kind", "FO")
    if dtxsid:
        pucs = PUC.objects.dtxsid_filter(dtxsid)
    else:
        pucs = PUC.objects.all()
    pucs = (
        pucs.filter(kind__code=kind)
        .with_num_products()
        .filter(cumulative_products__gt=0)
        .values(
            "id",
            "kind",
            "gen_cat",
            "prod_fam",
            "prod_type",
            "num_products",
            "cumulative_products",
        )
        .astree()
    )
    for puc in pucs.values():
        # We only needed gen_cat, prod_fam, prod_type to build the tree - now they are implicit in the structure
        puc.pop("gen_cat")
        puc.pop("prod_fam")
        puc.pop("prod_type")
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


def download_LPKeywords(request):
    """This view gets called to download all of the list presence keywords 
    and their definitions in a csv form.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="ListPresenceKeywords.csv"'
    writer = csv.writer(response)
    cols = ["Keyword", "Definition", "Kind"]
    writer.writerow(cols)
    LPKeywords = ExtractedListPresenceTag.objects.all()
    for keyword in LPKeywords:
        row = [keyword.name, keyword.definition, keyword.kind]
        writer.writerow(row)

    return response


def download_FunctionalUseCategories(request):
    """This view gets called to download all the functional use categories in a csv form.
    """
    response = HttpResponse(content_type="text/csv")
    response[
        "Content-Disposition"
    ] = 'attachment; filename="FunctionalUseCategories.csv"'
    writer = csv.writer(response)
    cols = ["Title", "Description", "Date Created"]
    writer.writerow(cols)
    categories = FunctionalUseCategory.objects.all()
    for category in categories:
        row = [
            category.title,
            category.description,
            category.created_at.strftime("%m/%d/%Y %H:%M:%S"),
        ]
        writer.writerow(row)

    return response
