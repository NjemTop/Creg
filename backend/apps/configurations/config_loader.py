import logging
from django.apps import apps
from urllib.parse import urljoin


logger = logging.getLogger(__name__)

def _get_model(model_name: str):
    return apps.get_model("configurations", model_name)


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


def get_integration_settings() -> dict:
    """
    Возвращает словарь с параметрами из IntegrationSettings.
    """
    try:
        IntegrationSettings = _get_model("IntegrationSettings")
        obj = IntegrationSettings.objects.first()
        if not obj:
            return {}

        return {
            # ——— Яндекс.Диск ——————————————————————————
            "YANDEX_DISK": {
                "OAUTH_TOKEN": obj.yandex_token,
                "CLIENT_ID": obj.yandex_client_id,
                "CLIENT_SECRET": obj.yandex_client_secret,
            },
            "YANDEX_DBS_TEAM": {
                "OAUTH_TOKEN": obj.yandex_dbs_token,
                "CLIENT_ID": obj.yandex_dbs_client_id,
                "CLIENT_SECRET": obj.yandex_dbs_client_secret,
            },
            "YANDEX_DISK_FOLDERS": obj.yandex_disk_folders,
            # ——— Файловые шары / SMB ————————————————
            "FILE_SHARE": {
                "USERNAME": obj.file_share_username,
                "PASSWORD": obj.file_share_password,
                "DOMAIN": obj.file_share_domain,
                "SMB_SERVER": obj.file_share_server,
            },
            # ——— Confluence / Nextcloud ——————————————
            "CONFLUENCE": {
                "URL": obj.confluence_url,
                "USERNAME": obj.confluence_username,
                "PASSWORD": obj.confluence_password,
            },
            "NEXT_CLOUD": {
                "URL": obj.nextcloud_url,
                "USER": obj.nextcloud_user,
                "PASSWORD": obj.nextcloud_password,
            },
            # ——— Telegram / TFS / Tickets / Alerts ————
            "TELEGRAM_SETTINGS": {
                "PROXY": obj.telegram_proxy,
                "BOT_ID": obj.telegram_bot_id,
                "BOT_TOKEN": obj.telegram_bot_token,
            },
            "TFS": {"ASSIGNED_TO_PRODUCT": obj.tfs_assigned_to_product},
            "TICKET_SETTINGS": {
                "API_ENDPOINT": obj.ticket_api_endpoint,
                "API_KEY": obj.ticket_api_key,
                "API_SECRET": obj.ticket_api_secret,
            },
            "SEND_ALERT": {
                "GROUP_SUPPORT_TEAM": obj.alert_group_support_team,
                "GROUP_RELEASE": obj.alert_group_release,
                "GROUP_TICKETS": obj.alert_group_tickets,
            },
        }
    except Exception as exc:
        logger.error("❌ Ошибка загрузки IntegrationSettings: %s", exc, exc_info=True)
        return {}


def get_smtp_settings() -> dict:
    """
    Возвращает настройки SMTP из первой включённой записи.
    """
    try:
        SMTPSettings = _get_model("SMTPSettings")
        obj = (
            SMTPSettings.objects.filter(enabled=True).first()
            or SMTPSettings.objects.first()
        )
        if not obj:
            return {}

        return {
            "SMTP": obj.smtp_host,
            "PORT": obj.smtp_port,
            "USER": obj.smtp_user or "",
            "PASSWORD": obj.smtp_password or "",
            "USE_TLS": obj.use_tls,
            "USE_SSL": obj.use_ssl,
            # «from» по умолчанию берём из имени пользователя
            "FROM": obj.smtp_user,
        }
    except Exception as exc:
        logger.error("❌ Ошибка загрузки SMTPSettings: %s", exc, exc_info=True)
        return {}
