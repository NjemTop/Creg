# middleware.py

from django.http import HttpResponseBadRequest

class AppendSlashWithPOSTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/') and request.method in ['POST', 'PATCH'] and request.path.endswith('/'):
            return HttpResponseBadRequest("URL не должен заканчиваться на слэш при отправке POST/PATCH-запроса. Используйте URL без завершающего слэша.")
        response = self.get_response(request)
        return response
