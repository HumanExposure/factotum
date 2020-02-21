from django.db import models
from django.core.exceptions import ValidationError
from .common_info import CommonInfo
from .product import Product
from .PUC import PUC


class ProductToPUC(CommonInfo):

    CLASSIFICATION_CHOICES = (
        ("MA", "Manual"),
        ("AU", "Automatic"),
        ("RU", "Rule Based"),
        ("MB", "Manual Batch"),
        ("BA", "Bulk Assignment"),
    )

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    puc = models.ForeignKey(PUC, on_delete=models.CASCADE)
    puc_assigned_usr = models.ForeignKey(
        "auth.User", on_delete=models.SET_NULL, null=True, blank=True
    )
    puc_assigned_script = models.ForeignKey(
        "Script", on_delete=models.SET_NULL, null=True, blank=True
    )
    classification_method = models.CharField(
        max_length=2, choices=CLASSIFICATION_CHOICES, null=False, default="MA"
    )
    classification_confidence = models.DecimalField(
        max_digits=6, decimal_places=3, default=1, null=True, blank=True
    )

    def __str__(self):
        return f"{self.product} --> {self.puc}"

    class Meta:
        unique_together = ("product", "puc", "classification_method")
