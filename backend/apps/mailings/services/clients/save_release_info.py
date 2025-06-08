from apps.clients.models import Client
from logger.log_config import scripts_info_logger, scripts_error_logger


def save_release_info(client_id, release_number, release_type, component_type, emails):
    """
    Сохраняет информацию об успешной рассылке.

    Args:
        client_id (int)
        release_number (str)
        release_type (str)
        component_type (str)
        emails (list)
    """
    try:
        client = Client.objects.get(pk=client_id)
        scripts_info_logger.info(
            f"Рассылка {release_number} ({release_type}/{component_type}) отправлена клиенту {client.client_name}: {emails}"
        )
    except Exception as e:
        scripts_error_logger.error(f"Ошибка логирования рассылки: {e}")
