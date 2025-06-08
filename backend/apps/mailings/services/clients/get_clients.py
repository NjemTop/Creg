from apps.clients.models import Client, Contact, TechnicalInfo
from logger.log_config import scripts_info_logger, scripts_error_logger


def get_clients_for_mailing(version_prefix):
    """
    Получает словарь активных клиентов и их контактов для рассылки.

    Args:
        version_prefix (str): Префикс версии продукта ("2" или "3").

    Returns:
        dict: {client_id: [email1, email2, ...]}
    """
    try:
        clients_for_mailing = {}

        active_clients = Client.objects.filter(contact_status=True)

        client_ids = TechnicalInfo.objects.filter(
            server_version__startswith=version_prefix,
            client__in=active_clients
        ).values_list('client_id', flat=True)

        for client_id in client_ids:
            emails = Contact.objects.filter(
                client_id=client_id,
                notification_update=True
            ).values_list('email', flat=True)

            if emails:
                clients_for_mailing[client_id] = list(emails)

        scripts_info_logger.info(f"Найдено {len(clients_for_mailing)} клиентов для рассылки.")
        return clients_for_mailing

    except Exception as e:
        scripts_error_logger.error(f"Ошибка при получении клиентов для рассылки: {e}")
        return {}
