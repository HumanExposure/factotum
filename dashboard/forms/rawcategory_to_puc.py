from django import forms
from django.db.models import Prefetch

from dashboard.models import PUC, DataGroup, DataDocument, ProductToPUC


class RawCategoryToPUCForm(forms.Form):
    puc = forms.ModelChoiceField(queryset=PUC.objects.all())
    datagroup = forms.ModelChoiceField(queryset=DataGroup.objects.all())
    raw_category = forms.ModelChoiceField(
        queryset=DataDocument.objects.values_list("raw_category", flat="True")
        .all()
        .distinct(),
        to_field_name="raw_category",
    )

    def clean(self):
        cleaned_data = super().clean()

        if self.errors:
            return False

        datagroup = cleaned_data.get("datagroup")
        raw_category = cleaned_data.get("raw_category")

        product_to_puc_queryset = ProductToPUC.objects.filter(
            classification_method="BA"
        )
        self.documents = (
            datagroup.datadocument_set.filter(raw_category=raw_category)
            .prefetch_related(
                Prefetch(
                    "products__producttopuc_set",
                    queryset=product_to_puc_queryset,
                    to_attr="bulk_assigned_p2p",
                )
            )
            .all()
        )

        if raw_category not in [document.raw_category for document in self.documents]:
            raise forms.ValidationError(
                {
                    "raw_category": "No Documents with that Raw Category in the "
                    "provided Data Group."
                }
            )
        self.products_as_set = set()
        for document in self.documents:
            for product in document.products.all():
                self.products_as_set.add(product)
        if not len(self.products_as_set):
            raise forms.ValidationError({"datagroup": "No Products will be affected."})

    def save(self):
        puc = self.cleaned_data.get("puc")
        product_to_puc_requires_update = []
        product_to_puc_requires_create = []

        # Split products into bulk create and bulk update lists
        # Assuming products will only have 1 Bulk Assigned puc
        for product in self.products_as_set:
            try:
                product_to_puc = product.bulk_assigned_p2p[0]
                product_to_puc.puc = puc
                product_to_puc_requires_update.append(product_to_puc)
            except IndexError:
                product_to_puc_requires_create.append(
                    ProductToPUC(product=product, classification_method="BA", puc=puc)
                )

        ProductToPUC.objects.bulk_create(product_to_puc_requires_create)
        ProductToPUC.objects.bulk_update(product_to_puc_requires_update, ["puc"])

        return {
            "products": self.products_as_set,
            "products_affected": len(self.products_as_set),
        }
