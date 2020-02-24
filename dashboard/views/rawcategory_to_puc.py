import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Exists, OuterRef
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView

from dashboard.forms import RawCategoryToPUCForm, ProductPUCForm
from dashboard.models import DataDocument, ProductDocument


class RawCategoryToPUCList(LoginRequiredMixin, ListView):
    template_name = "product_curation/rawcategory/rawcategory_to_puc.html"
    additional_context = {}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProductPUCForm()
        context["success_messages"] = self.additional_context.get("success_messages")
        context["form_errors"] = self.additional_context.get("form_errors")
        return context

    def get_queryset(self):
        return list(
            DataDocument.objects.annotate(
                has_products=Exists(
                    ProductDocument.objects.filter(document=OuterRef("pk"))
                )
            )
            .filter(has_products=True)
            .values("data_group__name", "data_group__id", "raw_category")
            .annotate(document_count=Count("raw_category"))
            .filter(document_count__gte=50)
            .exclude(raw_category__isnull=False, raw_category="")
            .order_by("-document_count")
        )

    def post(self, request):
        """
        :param request:
            Body {
                    "datagroup_rawcategory_sets": [
                        {"datagroup": int, "raw_category": str},
                        { . . . },
                    ],
                    "puc": int
                }
        :return: HttpResponseRedirect
        """
        datagroup_rawcategory_groups = json.loads(
            request.POST.get("datagroup_rawcategory_groups") or "{}"
        )
        self.additional_context["success_messages"] = []
        self.additional_context["form_errors"] = []

        if not datagroup_rawcategory_groups:
            self.additional_context["form_errors"].append(
                {"error_group": f"No Rows Selected"}
            )
            return HttpResponseRedirect(reverse("rawcategory_to_puc"))
        for datagroup_rawcategory_group in datagroup_rawcategory_groups:
            datagroup_rawcategory_group.update({"puc": request.POST.get("puc")})
            form = RawCategoryToPUCForm(datagroup_rawcategory_group)
            if form.is_valid():
                save_response = form.save()
                self.additional_context["success_messages"].append(
                    f"{form.cleaned_data.get('datagroup').name} - "
                    f"{form.cleaned_data.get('raw_category')} was saved. "
                    f"{save_response['products_affected']} products affected"
                )
            else:
                self.additional_context["form_errors"].append(
                    {
                        "error_group": f"Data Group: "
                        f"{datagroup_rawcategory_group['datagroup']} - "
                        f"{datagroup_rawcategory_group['raw_category']}",
                        "error_list": form.errors,
                    }
                )
        return HttpResponseRedirect(reverse("rawcategory_to_puc"))
