from taggit.managers import TaggableManager

from django.db import models
from django.urls import reverse
from django.db.models import Max

from .common_info import CommonInfo
from .extracted_text import ExtractedText
from .data_source import DataSource
from .source_category import SourceCategory


class ProductManager(models.Manager):
    def next_upc(self):
        return "stub_" + str(Product.objects.all().aggregate(Max("id"))["id__max"] + 1)


class Product(CommonInfo):
    documents = models.ManyToManyField(
        through="dashboard.ProductDocument",
        to="dashboard.DataDocument",
        help_text=("Data Documents related to this Product"),
    )
    tags = TaggableManager(
        through="dashboard.ProductToTag",
        to="dashboard.PUCTag",
        help_text=("A set of PUC Tags applicable " "to this Product"),
    )
    source_category = models.ForeignKey(
        SourceCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text=("The category assigned in " "the product's data source"),
    )
    title = models.CharField(max_length=255)
    manufacturer = models.CharField(
        db_index=True,
        max_length=250,
        null=True,
        blank=True,
        default="",
        help_text="title",
    )
    upc = models.CharField(
        db_index=True,
        max_length=60,
        null=False,
        blank=False,
        unique=True,
        help_text="UPC",
    )
    url = models.CharField(max_length=500, null=True, blank=True, help_text="URL")
    brand_name = models.CharField(
        db_index=True,
        max_length=200,
        null=True,
        blank=True,
        default="",
        help_text="brand name",
    )
    size = models.CharField(max_length=100, null=True, blank=True, help_text="size")
    model_number = models.CharField(
        max_length=200, null=True, blank=True, help_text="model number"
    )
    color = models.CharField(max_length=100, null=True, blank=True, help_text="color")
    item_id = models.IntegerField(null=True, blank=True, help_text="item ID")
    parent_item_id = models.IntegerField(
        null=True, blank=True, help_text="parent item ID"
    )
    short_description = models.TextField(
        null=True, blank=True, help_text="short description"
    )
    long_description = models.TextField(
        null=True, blank=True, help_text="long description"
    )
    thumb_image = models.CharField(
        max_length=500, null=True, blank=True, help_text="thumbnail image"
    )
    medium_image = models.CharField(
        max_length=500, null=True, blank=True, help_text="medium image"
    )
    large_image = models.CharField(
        max_length=500, null=True, blank=True, help_text="large image"
    )
    objects = ProductManager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"pk": self.pk})

    def get_uber_product_to_puc(self):
        pucs = self.producttopuc_set
        if pucs.filter(classification_method="MA").exists():
            return pucs.filter(classification_method="MA").first()
        elif pucs.filter(classification_method="MB").exists():
            return pucs.filter(classification_method="MB").first()
        elif pucs.filter(classification_method="RU").exists():
            return pucs.filter(classification_method="RU").first()
        elif pucs.filter(classification_method="AU").exists():
            return pucs.filter(classification_method="AU").first()
        else:
            return None

    def get_uber_puc(self):
        thispuc = self.get_uber_product_to_puc()
        if thispuc:
            return thispuc.puc
        else:
            return None

    @property
    def uber_puc(self):
        thispuc = self.get_uber_product_to_puc()
        if thispuc:
            return thispuc.puc
        else:
            return None

    def get_tag_list(self):
        return u", ".join(o.name for o in self.tags.all())

    # returns list of valid puc_tags
    def get_puc_tag_list(self):
        all_uber_tags = self.get_uber_product_to_puc().puc.tags.all()
        return u", ".join(o.name for o in all_uber_tags)

    # returns set of valid puc_tags
    def get_puc_tags(self):
        return self.get_uber_product_to_puc().puc.tags.all()

    @property
    def rawchems(self):
        """A generator of all RawChem objects in this product

        It's recommended to first "prefetch_related" the RawChem objects:
            Product.objecs.prefetch_related("datadocument_set__extractedtext__rawchem")
        """
        for doc in self.datadocument_set.all():
            try:
                yield from doc.extractedtext.rawchem.all()
            except ExtractedText.DoesNotExist:
                pass

    class Meta:
        ordering = ["-created_at"]
