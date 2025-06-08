import logging
from django.shortcuts import redirect
from django.conf import settings

logger = logging.getLogger(__name__)

EXCLUDED_PATHS = [
    settings.LOGIN_URL,
    "/auth/local-login/",
    "/auth/oidc-login/",
    "/oidc/authenticate/",
    "/oidc/callback/",
    "/oidc/logout/",
    "/static/",
    "/media/"
]

class LoginRequiredMiddleware:
    """Middleware для редиректа неавторизованных пользователей на страницу входа."""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated:
            if not any(request.path.startswith(path) for path in EXCLUDED_PATHS):
                logger.info(f"🔒 Неавторизованный доступ: {request.path} → редирект на {settings.LOGIN_URL}")
                return redirect(settings.LOGIN_URL)
            else:
                logger.debug(f"✅ Доступ разрешён без авторизации: {request.path}")
        
        return self.get_response(request)
