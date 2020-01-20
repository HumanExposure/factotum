# Celery Results View

A simple Django view to get the results back from from your Celery tasks.

## How it works

You can `GET` or `DELETE` this view by passing in a comma-separated list of task IDs. The endpoint will efficiently fetch or forget these tasks.

## How to use

Include `"celery_resultsview.urls"` your `urls.py` file:

```python
...

urlpatterns = [
    ...
    url(r"^api/tasks/", include("celery_resultsview.urls")),
]
```
