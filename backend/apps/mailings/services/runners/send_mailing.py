from apps.mailings.services.base.email_sender import EmailSender
from apps.mailings.services.clients.get_clients import get_clients_for_mailing
from apps.mailings.services.utils.attachments import clear_attachments_directory
from apps.mailings.services.clients.save_release_info import save_release_info
from logger.log_config import scripts_info_logger, scripts_error_logger


def send_mailing(mailing_type, release_type, server_version=None, ipad_version=None, android_version=None):
    if server_version:
        component_type = 'server'
        version_to_use = server_version
    elif ipad_version:
        component_type = 'ipad'
        version_to_use = ipad_version
    elif android_version:
        component_type = 'android'
        version_to_use = android_version
    else:
        raise ValueError("Не указана ни одна версия для рассылки.")

    clear_attachments_directory()

    sender = EmailSender(
        emails=None,
        mailing_type=mailing_type,
        release_type=release_type,
        server_version=server_version,
        ipad_version=ipad_version,
        android_version=android_version
    )

    clients_contacts = get_clients_for_mailing(release_type[-2])
    if not clients_contacts:
        return 'Нет контактов для рассылки.'

    mail_config = sender.config['MAIL_SETTINGS_SUPPORT']
    successful, failed = 0, 0

    import smtplib
    with smtplib.SMTP(mail_config['SMTP'], 587) as smtp:
        smtp.starttls()
        smtp.login(mail_config['USER'], mail_config['PASSWORD'])

        for client_id, emails in clients_contacts.items():
            try:
                msg = sender.build_message_for_client(client_id, emails)
                smtp.send_message(msg)
                save_release_info(client_id, version_to_use, release_type, component_type, emails)
                successful += 1
            except Exception as e:
                scripts_error_logger.error(f"Ошибка рассылки клиенту {client_id}: {e}")
                failed += 1

    return f"Успешно: {successful}, Ошибки: {failed}"
