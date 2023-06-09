from django.http import HttpResponseBadRequest
import logging

logger = logging.getLogger(__name__)

class ExceptionLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except Exception as error_message:
            logger.exception(f'Системная ошибка: {error_message}')
            raise error_message

        return response

class AppendSlashWithPOSTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_exception_endpoint_clients = request.path.startswith('/api/clients/') and request.path.count('/') == 4
        is_exception_endpoint_release = request.path.startswith('/api/data_release/') and request.path.count('/') == 3
        is_exception_endpoint_report = request.path.startswith('/api/report/') and request.path.count('/') == 3  # добавлено

        if request.path.startswith('/api/') and request.method in ['POST', 'PATCH'] and request.path.endswith('/') and not (is_exception_endpoint_clients or is_exception_endpoint_release or is_exception_endpoint_report):  # добавлено
            return HttpResponseBadRequest("URL не должен заканчиваться на слэш при отправке POST/PATCH-запроса. Используйте URL без завершающего слэша.")
        response = self.get_response(request)
        return response
