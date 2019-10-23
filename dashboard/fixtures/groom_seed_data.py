# drop and replace schema local_factotum

######## At the command prompt:
""" 
python manage.py migrate
python manage.py loaddata prod_20180328
python manage.py loaddata 00_superuser 
"""

from django.contrib.auth.models import User
from dashboard.models import (
    DataGroup,
    ExtractedText,
    ProductToPUC,
    Taxonomy,
    TaxonomySource,
    PUC,
    DataDocument,
    ExtractedChemical,
    ProductDocument,
)
from django.db.models import Count
from random import sample


# prep the objects by switching their related user to Karyn
karyn = User.objects.get(username="Karyn")

DataGroup.objects.values("downloaded_by__username").annotate(n=Count("id"))
DataGroup.objects.all().update(downloaded_by=karyn)

ExtractedText.objects.values("qa_approved_by__username").annotate(
    n=Count("data_document_id")
)

ProductToPUC.objects.values("puc_assigned_usr__username").annotate(n=Count("id"))
ProductToPUC.objects.filter(puc_assigned_usr_id__gt=1).update(puc_assigned_usr=karyn)

PUC.objects.values("last_edited_by__username").order_by("last_edited_by").annotate(
    n=Count("id")
)

TaxonomySource.objects.values("last_edited_by__username").order_by(
    "last_edited_by"
).annotate(n=Count("id"))
Taxonomy.objects.values("last_edited_by__username").order_by("last_edited_by").annotate(
    n=Count("id")
)

# Remove all the real-world users
User.objects.exclude(username="Karyn").delete()

DataDocument.objects.exclude(
    id__in=ProductDocument.objects.all().values("document_id")
).count()

# select a lot of random data documents, then delete them
dd_list = DataDocument.objects.values_list("id", flat=True)
dd_list = list(dd_list)
random_list = sample(dd_list, min(len(dd_list), 70000))
DataDocument.objects.filter(id__in=random_list).delete()
# Delete the corresponding ExtractedText objects
ExtractedText.objects.filter(data_document_id__in=random_list).delete()

#
exchem_list = ExtractedChemical.objects.all().values_list("extracted_text", flat=True)
random_list = sample(exchem_list, min(len(exchem_list), 8000))
ExtractedChemical.objects.filter(id__in=random_list).delete()

DataDocument.objects.all.count()

# delete the datadocuments that don't have related extractedchemicals
DataDocument.objects.exclude(
    id__in=ExtractedChemical.objects.all().values("extracted_text")
).delete()

######## At the command prompt:

""" 
python manage.py dumpdata dashboard.grouptype dashboard.dsstoxlookup dashboard.documenttype dashboard.unittype dashboard.weightfractiontype dashboard.puctag --format=yaml > ./dashboard/fixtures/01_lookups.yaml
python manage.py dumpdata dashboard.datasource --format=yaml > ./dashboard/fixtures/02_datasource.yaml
python manage.py dumpdata dashboard.datagroup --format=yaml > ./dashboard/fixtures/03_datagroup.yaml
python manage.py dumpdata dashboard.PUC --format=yaml > ./dashboard/fixtures/04_PUC.yaml
python manage.py dumpdata dashboard.product --format=yaml > ./dashboard/fixtures/05_product.yaml
python manage.py dumpdata dashboard.datadocument  --format=yaml > ./dashboard/fixtures/06_datadocument.yaml
python manage.py dumpdata dashboard.extractedtext dashboard.extractedcpcat dashboard.extractedhhdoc dashboard.rawchem dashboard.extractedchemical dashboard.extractedfunctionaluse dashboard.extractedlistpresence dashboard.extractedhhrec --format=yaml > ./dashboard/fixtures/07_rawchem_etc.yaml
python manage.py dumpdata dashboard.script --format=yaml > ./dashboard/fixtures/08_script.yaml
python manage.py dumpdata dashboard.productdocument --format=yaml > ./dashboard/fixtures/09_productdocument.yaml

python manage.py dumpdata dashboard.extractedhabitsandpractices --format=yaml > ./dashboard/fixtures/10_habits_and_practices.yaml

python manage.py dumpdata dashboard.extractedhabitsandpracticestopuc --format=yaml > ./dashboard/fixtures/11_habits_and_practices_to_puc.yaml
python manage.py dumpdata dashboard.producttopuc --format=yaml > ./dashboard/fixtures/12_product_to_puc.yaml
python manage.py dumpdata dashboard.puctag dashboard.producttotag dashboard.puctotag --format=yaml > ./dashboard/fixtures/13_puc_tag.yaml
python manage.py dumpdata dashboard.extractedlistpresencetag --format=yaml > ./dashboard/fixtures/14_list_presence_tag.yaml
python manage.py dumpdata dashboard.extractedlistpresencetotag --format=yaml > ./dashboard/fixtures/15_list_presence_to_tag.yaml

"""
