import os

from django.http import HttpResponse
from django.views.generic.base import TemplateView, View

import _jsonnet as jsonnet

from dashboard.forms.data_group import ProductBulkCSVFormSet
from factotum.environment import env


class RedocView(TemplateView):
    """The Redoc documentation."""

    template_name = "redoc.html"


class OpenAPIView(View):
    """The OpenAPI spec file."""

    http_method_names = ["get"]

    base_spec = jsonnet.evaluate_file(
        os.path.join(os.path.dirname(__file__), "schemas", "schema.jsonnet"),
        ext_vars={
            "baseServer": "__BASE_SERVER__",
            "version": env.FACTOTUM_WS_VERSION_NUMBER,
            "product_csv_headers": "".join(
                [f"\n- {col}" for col in ProductBulkCSVFormSet.header_cols]
            ),
        },
        jpathdir=os.path.join(os.path.dirname(__file__), "schemas"),
    )

    def get(self, request, *args, **kwargs):
        return HttpResponse(self.base_spec, content_type="application/json")
