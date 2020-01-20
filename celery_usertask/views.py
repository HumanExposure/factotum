from celery_usertask.models import UserTaskLog
from django.http import JsonResponse


def get_jobs(request):
    if request.user.is_anonymous:
        return JsonResponse([], safe=False)
    else:
        logs = UserTaskLog.objects.filter(user=request.user)
        return JsonResponse([log for log in logs.values("task", "name")], safe=False)
