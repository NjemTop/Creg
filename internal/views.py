from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from scripts.confluence.get_info_release import get_server_release_notes, get_ipad_release_notes, get_android_release_notes
from django.conf import settings
from django.urls import URLPattern, URLResolver, get_resolver, reverse
import os
from django.template import TemplateDoesNotExist
from django.http import JsonResponse
from celery.result import AsyncResult
from django_celery_results.models import TaskResult
from internal.tasks import echo, send_test_email, analyze_logs_task


@staff_member_required
def internal_index(request):
    urls = []
    resolver = get_resolver()
    url_patterns = resolver.url_patterns
    
    def extract_urls(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLPattern) and pattern.name:
                if pattern.name.startswith('internal_'):
                    urls.append(pattern.name)
            elif isinstance(pattern, URLResolver):
                extract_urls(pattern.url_patterns, prefix + pattern.pattern._route)

    extract_urls(url_patterns)
    return render(request, 'internal/index.html', {'urls': urls})

@staff_member_required
def release_notes_page(request):
    try:
        return render(request, 'internal/release_notes.html')
    except TemplateDoesNotExist as e:
        raise Exception(f"Template does not exist: {e}, current dir: {os.getcwd()}, template dirs: {settings.TEMPLATES[0]['DIRS']}")

@staff_member_required
@require_GET
def release_notes(request):
    version_id = request.GET.get('version_id')
    platform = request.GET.get('platform')

    if not version_id or not platform:
        return JsonResponse({'error': 'version_id и platform являются обязательными параметрами'}, status=400)

    try:
        if platform.lower() == 'server':
            updates = get_server_release_notes(version_id)
        elif platform.lower() == 'ipad':
            updates = get_ipad_release_notes(version_id)
        elif platform.lower() == 'android':
            updates = get_android_release_notes(version_id)
        else:
            return JsonResponse({'error': 'Неверная платформа. Используйте server, ipad или android'}, status=400)

        return JsonResponse({'version_id': version_id, 'platform': platform, 'updates': updates}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def show_log_download(request):
    return render(request, 'main/report/artifactory_downloads_log.html')

def get_log_analysis_data(request):
    task = analyze_logs_task.delay()  # Запускаем задачу в фоне
    return JsonResponse({'task_id': task.id})  # Возвращаем ID задачи на фронтенд

def get_task_status(request, task_id):
    task_result = AsyncResult(task_id)  # Получаем результат задачи по ID
    if task_result.state == 'PENDING':
        response = {'status': 'PENDING'}
    elif task_result.state == 'STARTED':
        response = {'status': 'STARTED', 'info': task_result.info}  # Возвращаем статус STARTED
    elif task_result.state == 'SUCCESS':
        response = {'status': 'SUCCESS', 'result': task_result.result}
    elif task_result.state == 'FAILURE':
        response = {'status': 'FAILURE', 'error': str(task_result.info)}
    else:
        response = {'status': task_result.state, 'info': str(task_result.info)}  # Обработка других статусов

    return JsonResponse(response)

def test_task(request):
    task = echo.delay(4, 4)
    result = AsyncResult(id=task.task_id)
    
    if result.failed():
        response = f"Task ID: {task.task_id}, Task Status: {result.status}, Error: {result.result}"
    else:
        response = f"Task ID: {task.task_id}, Task Status: {result.status}, Task Result: {result.result}"
    
    return HttpResponse(response)

def test_send_email_task(request):
    task = send_test_email.delay('oleg.eliseev@boardmaps.ru')
    return JsonResponse({'task_id': task.id}, status=202)

def task_results(request):
    results = TaskResult.objects.all()
    return render(request, 'main/test/task_results.html', {'results': results})
