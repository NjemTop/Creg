from apps.configurations.config_loader import (
    get_integration_settings,
    get_smtp_settings,
)


def get_combined_config() -> dict:
    """
    Собирает единый конфиг для сервисов рассылки.

    • Интеграционные параметры берутся из таблицы IntegrationSettings.  
    • SMTP-параметры — из первой включённой записи SMTPSettings (или первой попавшейся,
      если ни одна не включена).

    Возвращает словарь, совместимый со старым форматом, в котором:
        -   'MAIL_SETTINGS'        — основной SMTP (используется send_email)
        -   'MAIL_SETTINGS_SUPPORT'— SMTP для писем саппорта (build_message_for_client)
        -   …остальные ключи       — как раньше, из IntegrationSettings

    Raises:
        ValueError: если в базе нет настроек SMTP.
    """
    integration = get_integration_settings()
    smtp = get_smtp_settings()
    if not smtp:
        raise ValueError("SMTP не настроен.")
    integration["MAIL_SETTINGS"] = smtp
    integration["MAIL_SETTINGS_SUPPORT"] = smtp
    return integration
