from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .common_info import CommonInfo
from .product_document import ProductDocument
from .PUC import PUC


def validate_prefix(value):
    if value[:6] != "DTXSID":
        raise ValidationError(
            _('%(value)s does not begin with "DTXSID"'), params={"value": value}
        )


def validate_blank_char(value):
    if " " in value:
        raise ValidationError(
            _("%(value)s cannot have a blank character"), params={"value": value}
        )


class DSSToxLookup(CommonInfo):

    sid = models.CharField(
        "DTXSID",
        max_length=50,
        null=False,
        blank=False,
        unique=True,
        validators=[validate_prefix, validate_blank_char],
    )
    true_cas = models.CharField("True CAS", max_length=50, null=True, blank=True)
    true_chemname = models.CharField(
        "True chemical name", max_length=500, null=True, blank=True
    )

    def __str__(self):
        return self.true_chemname

    def get_absolute_url(self):
        return reverse("chemical", kwargs={"sid": self.sid})

    @property
    def puc_count(self):
        pdocs = ProductDocument.objects.from_chemical(self)
        return PUC.objects.filter(products__in=pdocs.values("product")).count()

    @property
    def cumulative_puc_count(self):
        pdocs = ProductDocument.objects.from_chemical(self)
        pucs = PUC.objects.filter(products__in=pdocs.values("product"))
        titles = []
        for puc in pucs:
            titles += list(f for f in (puc.gen_cat, puc.prod_fam, puc.prod_type) if f)
        return len(set(titles))
