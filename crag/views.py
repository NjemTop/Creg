from django.http import JsonResponse
from celery import Celery


app = Celery('crag')

def healthz(request):
    return JsonResponse({"status": "ok"})


def healthz_worker(request):
    try:
        app.control.inspect().ping()
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "failed", "error": str(e)}, status=500)
