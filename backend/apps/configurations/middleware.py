from django.contrib.sites.models import Site

class BaseURLMiddleware:
    """Добавляет BASE_URL во все запросы"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.BASE_URL = f"https://{Site.objects.get_current().domain}"
        return self.get_response(request)
