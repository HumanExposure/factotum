from django.conf.urls import url
from celery_resultsview.views import CeleryResultsView

app_name = "celery_resultsview"
urlpatterns = [
    url(
        r"^(?P<task_ids>[\w\-\,]+)/$",
        CeleryResultsView.as_view(),
        name="CeleryResultsView",
    )
]
