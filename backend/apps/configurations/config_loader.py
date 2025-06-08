import logging
from django.apps import apps
from urllib.parse import urljoin


logger = logging.getLogger(__name__)

def get_oidc_settings():
    """Получает OIDC настройки из базы, если OIDC включен"""
    try:
        OIDCSettings = apps.get_model("configurations", "OIDCSettings")  # Загружаем модель "по требованию"
        oidc_config = OIDCSettings.objects.filter(enabled=True).first()

        if not oidc_config:
            return None  # OIDC выключен, не загружаем настройки

        return {
            "KEYCLOAK_BASE_URL": oidc_config.keycloak_base_url,
            "KEYCLOAK_REALM": oidc_config.realm,
            "KEYCLOAK_CLIENT_ID": oidc_config.client_id,
            "KEYCLOAK_CLIENT_SECRET": oidc_config.client_secret,
            "OIDC_OP_AUTHORIZATION_ENDPOINT": urljoin(oidc_config.keycloak_base_url, f"realms/{oidc_config.realm}/protocol/openid-connect/auth"),
            "OIDC_OP_TOKEN_ENDPOINT": urljoin(oidc_config.keycloak_base_url, f"realms/{oidc_config.realm}/protocol/openid-connect/token"),
            "OIDC_OP_USER_ENDPOINT": urljoin(oidc_config.keycloak_base_url, f"realms/{oidc_config.realm}/protocol/openid-connect/userinfo"),
            "OIDC_OP_JWKS_ENDPOINT": urljoin(oidc_config.keycloak_base_url, f"realms/{oidc_config.realm}/protocol/openid-connect/certs"),
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки OIDC настроек: {e}")
        return None  # Безопасный fallback


def get_smtp_settings():
    """Получает SMTP настройки из базы, если SMTP включен"""
    try:
        SMTPSettings = apps.get_model("configurations", "SMTPSettings")
        smtp_config = SMTPSettings.objects.filter(enabled=True).first()

        if not smtp_config:
            return None  # Если SMTP выключен, ничего не загружаем

        return {
            "EMAIL_HOST": smtp_config.smtp_host,
            "EMAIL_PORT": smtp_config.smtp_port,
            "EMAIL_HOST_USER": smtp_config.smtp_user,
            "EMAIL_HOST_PASSWORD": smtp_config.smtp_password,
            "EMAIL_USE_TLS": smtp_config.use_tls,
            "EMAIL_USE_SSL": smtp_config.use_ssl,
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки SMTP настроек: {e}")
        return None
