from django.db import models
from django.core.exceptions import ValidationError
from .common_info import CommonInfo
from .product import Product
from .PUC import PUC


class ProductToPUC(CommonInfo):
    MANUAL = 'MA'
    AUTOMATIC = 'AU'
    CLASSIFICATION_CHOICES = (
        (MANUAL, 'Manual'),
        (AUTOMATIC, 'Automatic'))

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    PUC = models.ForeignKey(PUC, on_delete=models.CASCADE)
    puc_assigned_usr = models.ForeignKey('auth.User',
                                         on_delete=models.SET_NULL, null=True, blank=True)
    puc_assigned_script = models.ForeignKey('Script',
                                            on_delete=models.SET_NULL, null=True, blank=True)
    puc_assigned_time = models.DateTimeField(null=True, blank=True)
    classification_method = models.CharField(max_length=2, choices=CLASSIFICATION_CHOICES, null=False, default='MA')
    classification_confidence = models.DecimalField(max_digits=6, decimal_places=3, default=1, null=True, blank=True)

    #def clean(self):
    #    print("Cleaning PtoPUC")
    #    print(self.classification_method)
    #    print(self.PUC)
    #    print(str(self.product.id))
    #    if ProductToPUC.objects.filter(product=self.product).count() > 0:
        #print(matching_prod.pk)
        #if matching_prod is not None:
    #        raise ValidationError("There is already a PUC assigned to this Product")

    def save(self, *args, **kwargs):
        print(self.product)
        print(ProductToPUC.objects.filter(product=self.product,
                                       classification_method='MA').count())
        if ProductToPUC.objects.filter(product=self.product,
                                       classification_method='MA').count() > 0:
            raise ValidationError("Too many manually linked PUCs!")
        else:
            super(ProductToPUC, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        if ProductToPUC.objects.filter(product=self.product,
                                       classification_method='MA').count() > 0:
            raise ValidationError("Too many manually linked PUCs!")
        super(ProductToPUC, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.id)
