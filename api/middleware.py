# middleware.py

from django.http import HttpResponseBadRequest

class AppendSlashWithPOSTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        is_exception_endpoint = request.path.startswith('/api/clients/') and request.path.count('/') == 4

        if request.path.startswith('/api/') and request.method in ['POST', 'PATCH'] and request.path.endswith('/') and not is_exception_endpoint:
            return HttpResponseBadRequest("URL не должен заканчиваться на слэш при отправке POST/PATCH-запроса. Используйте URL без завершающего слэша.")
        response = self.get_response(request)
        return response
