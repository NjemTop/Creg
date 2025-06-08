from apps.clients.models import Client
import logging

logger = logging.getLogger(__name__)


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
        logger.info(
            "Рассылка %s (%s/%s) отправлена клиенту %s: %s",
            release_number,
            release_type,
            component_type,
            client.client_name,
            emails,
        )
    except Exception as e:
        logger.error("Ошибка логирования рассылки: %s", e)
