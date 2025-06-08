import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.models import Site
from urllib.parse import urljoin, urlencode
from apps.configurations.config_loader import get_oidc_settings

logger = logging.getLogger(__name__)


def login_view(request):
    """Страница входа. Передаём в шаблон, включена ли интеграция с Keycloak"""
    oidc_settings = get_oidc_settings()
    return render(request, "authentication/login.html", {"oidc_enabled": bool(oidc_settings)})

def logout_view(request):
    """Выход из системы: если вход был через Keycloak, редиректим на Keycloak logout, иначе — локальный выход."""

    base_url = f"{Site.objects.get_current().domain}"

    # Определяем способ аутентификации пользователя
    is_oidc_session = "oidc_access_token" in request.session
    id_token = request.session.get("oidc_id_token")

    username = request.user.username if request.user.is_authenticated else "Аноним"

    logger.info(f"🔄 Выход пользователя: {username}, через OIDC: {is_oidc_session}")

    logout(request)  # Выход из Django-сессии

    # Если пользователь зашёл через Keycloak → отправляем на OIDC logout
    if is_oidc_session and id_token:
        logout_url = (
            f"{settings.OIDC_OP_LOGOUT_ENDPOINT}?"
            + urlencode({"post_logout_redirect_uri": base_url, "id_token_hint": id_token})
        )
        logger.info(f"🔀 OIDC-logout: редирект на {logout_url}")
        return redirect(logout_url)

    # Если OIDC выключен или вход был локальный → редирект на главную
    logger.info("🏠 Локальный выход: редирект на главную страницу")
    return redirect("/")

def oidc_login(request):
    """Перенаправляет пользователя на страницу авторизации Keycloak."""
    if not settings.OIDC_OP_AUTHORIZATION_ENDPOINT:
        logger.warning("⚠️ OIDC отключен, редирект на локальный вход")
        return redirect("/auth/login/")

    return redirect(reverse("oidc_authentication_init"))

def local_login_view(request):
    """Обрабатывает локальный вход через Django"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user_ip = request.META.get("REMOTE_ADDR", "unknown")  # Получаем IP

        logger.info(f"🔑 Попытка входа: username={username}, IP={user_ip}")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            logger.info(f"✅ Успешный вход: {user.username}, IP={user_ip}, is_active={user.is_active}")
            login(request, user)
            messages.success(request, "Вы успешно вошли!")
            return redirect("/")
        else:
            # Проверяем, существует ли пользователь
            from django.contrib.auth.models import User
            if User.objects.filter(username=username).exists():
                logger.warning(f"❌ Ошибка входа: username={username}, неверный пароль, IP={user_ip}")
            else:
                logger.warning(f"❌ Ошибка входа: username={username}, пользователь не найден, IP={user_ip}")
            messages.error(request, "Неверные учетные данные!")

    return redirect("/auth/login/")
