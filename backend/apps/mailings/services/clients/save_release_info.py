from main.models import ReleaseInfo, ClientsList
from django.utils import timezone
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
        client = ClientsList.objects.get(pk=client_id)
        ReleaseInfo.objects.create(
            date=timezone.now().date(),
            release_number=release_number,
            release_type=release_type,
            component_type=component_type,
            client_name=client.client_name,
            client_email=emails
        )
        scripts_info_logger.info(
            f"Запись в ReleaseInfo сохранена: {client.client_name} ({release_number})"
        )
    except Exception as e:
        scripts_error_logger.error(f"Ошибка при сохранении ReleaseInfo: {e}")
