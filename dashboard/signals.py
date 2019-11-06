import os
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete, pre_save, pre_delete
from django.db.backends.signals import connection_created
from crum import get_current_user
import shutil

from dashboard.models import (
    ProductToPUC,
    ProductToTag,
    PUCToTag,
    RawChem,
    ExtractedChemical,
    ExtractedListPresence,
    ExtractedFunctionalUse,
    DataDocument,
    DataGroup,
    DocumentTypeGroupTypeCompatibilty,
    Product,
    ProductDocument,
)

# When dissociating a product from a PUC, delete it's (PUC-dependent) tags
@receiver(pre_delete, sender=ProductToPUC)
def delete_product_puc_tags(sender, **kwargs):
    instance = kwargs["instance"]
    ProductToTag.objects.filter(content_object=instance.product).delete()


# When dissociating a puc from a tag, also disocciate any puc-related products from that tag
@receiver(post_delete, sender=PUCToTag)
def delete_related_product_tags(sender, **kwargs):
    instance = kwargs["instance"]
    products = instance.content_object.products.all()
    products_to_tags = ProductToTag.objects.filter(tag=instance.tag).filter(
        content_object__in=products
    )
    products_to_tags.delete()


@receiver(pre_save, sender=RawChem)
@receiver(pre_save, sender=ExtractedChemical)
@receiver(pre_save, sender=ExtractedListPresence)
@receiver(pre_save, sender=ExtractedFunctionalUse)
def uncurate(sender, **kwargs):
    instance = kwargs.get("instance")
    watched_keys = {"raw_cas", "raw_chem_name"}
    if not instance.tracker.changed().keys().isdisjoint(watched_keys):
        instance.dsstox = None
        instance.rid = None


@receiver(post_delete, sender=DocumentTypeGroupTypeCompatibilty)
def rm_invalid_doctypes(sender, **kwargs):
    """When a DocumentTypeGroupTypeCompatibilty is dropped, the newly invalid DocumentType
    fields of affected DataDocuments need to be made unidentified.
    """
    compat_obj = kwargs["instance"]
    doc_type = compat_obj.document_type
    group_type = compat_obj.group_type
    (
        DataDocument.objects.filter(
            document_type=doc_type, data_group__group_type=group_type
        ).update(document_type=doc_type._meta.model.objects.get(code="UN"))
    )


@receiver(models.signals.post_delete, sender=DataGroup)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes datagroup directory from filesystem
    when datagroup instance is deleted.
    """
    dg_folder = instance.get_dg_folder()
    if os.path.isdir(dg_folder):
        shutil.rmtree(dg_folder, ignore_errors=True)


@receiver(models.signals.post_delete, sender=ProductDocument)
def auto_delete_orphaned_products_on_delete(sender, instance, **kwargs):
    """
    Deletes orphaned products on ProductDocument delete
    """
    Product.objects.exclude(
        id__in=ProductDocument.objects.values("product_id")
    ).delete()


@receiver(connection_created)
def new_connection(sender, connection, **kwargs):
    user = get_current_user()
    # set current user for the session
    if user:
        connection.cursor().execute("SET @current_user = %s", [user.id])
