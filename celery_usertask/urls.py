from django.conf.urls import url
from celery_usertask.views import get_jobs

app_name = "celery_usertask"
urlpatterns = [url(r"^$", get_jobs, name="get_jobs")]
