import celery
from django.http import JsonResponse, HttpResponse
from django.views import View

try:
    from celery_usertask.models import UserTaskLog
except ImportError:
    UserTaskLog = None


class CeleryResultsView(View):
    def __init__(self):
        self.app = celery.current_app

    def _get_task_keys(self, task_ids_str):
        task_ids = task_ids_str.split(",")
        return [self.app.backend.get_key_for_task(i) for i in task_ids]

    def _get_single_result(self, task_key):
        task_status_verbose = self.app.backend.get(task_key)
        decoded = self.app.backend.decode(task_status_verbose)
        return {decoded["task_id"]: decoded}

    def _get_many_results(self, task_keys):
        task_status = {}
        try:
            task_status_verbose = self.app.backend.mget(task_keys)
            if task_status_verbose == [None]:
                return task_status
            elif isinstance(task_status_verbose, dict):
                values = task_status_verbose.values()
            elif isinstance(task_status_verbose, list):
                values = task_status_verbose
            else:
                raise NotImplementedError
            for value in values:
                if value:
                    decoded = self.app.backend.decode(value)
                    task_status[decoded["task_id"]] = decoded
        except NotImplementedError:
            for task_key in task_keys:
                task_status.update(self._get_single_result(task_key))

        return task_status

    def get(self, request, task_ids):
        task_keys = self._get_task_keys(task_ids)
        data = self._get_many_results(task_keys)
        return JsonResponse(data)

    def delete(self, request, task_ids):
        task_ids = task_ids.split(",")
        async_results = [self.app.AsyncResult(i) for i in task_ids]
        result_set = self.app.ResultSet(async_results)
        result_set.forget()
        response = HttpResponse()
        if UserTaskLog:
            UserTaskLog.objects.filter(task__in=task_ids).delete()
        response.status_code = 204
        return response
