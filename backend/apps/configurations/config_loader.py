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


def get_integration_settings():
    """Получает настройки интеграций из базы"""
    try:
        IntegrationSettings = apps.get_model("configurations", "IntegrationSettings")
        settings_obj = IntegrationSettings.objects.first()
        if not settings_obj:
            return {}
        return {
            "YANDEX_DISK": {
                "OAUTH-TOKEN": settings_obj.yandex_token,
                "CLIENT_ID": settings_obj.yandex_client_id,
                "CLIENT_SECRET": settings_obj.yandex_client_secret,
            },
            "YANDEX_DBS_TEAM": {
                "OAUTH-TOKEN": settings_obj.yandex_dbs_token,
                "CLIENT_ID": settings_obj.yandex_dbs_client_id,
                "CLIENT_SECRET": settings_obj.yandex_dbs_client_secret,
            },
            "YANDEX_DISK_FOLDERS": settings_obj.yandex_disk_folders,
            "FILE_SHARE": {
                "USERNAME": settings_obj.file_share_username,
                "PASSWORD": settings_obj.file_share_password,
                "DOMAIN": settings_obj.file_share_domain,
                "SMB_SERVER": settings_obj.file_share_server,
            },
            "CONFLUENCE": {
                "USERNAME": settings_obj.confluence_username,
                "PASSWORD": settings_obj.confluence_password,
            },
            "NEXT_CLOUD": {
                "URL": settings_obj.nextcloud_url,
                "USER": settings_obj.nextcloud_user,
                "PASSWORD": settings_obj.nextcloud_password,
            },
            "TELEGRAM_SETTINGS": {
                "PROXY": settings_obj.telegram_proxy,
                "BOT_ID": settings_obj.telegram_bot_id,
                "BOT_TOKEN": settings_obj.telegram_bot_token,
            },
            "TFS": {
                "assigned_to_product": settings_obj.tfs_assigned_to_product,
            },
            "TICKET_SETTINGS": {
                "API_ENDPOINT": settings_obj.ticket_api_endpoint,
                "API_KEY": settings_obj.ticket_api_key,
                "API_SECRET": settings_obj.ticket_api_secret,
            },
            "SEND_ALERT": {
                "GROUP_SUPPOR_TEAM": settings_obj.alert_group_support_team,
                "GROUP_RELEASE": settings_obj.alert_group_release,
                "GROUP_TICKETS": settings_obj.alert_group_tickets,
            },
        }
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки интеграционных настроек: {e}")
        return {}
