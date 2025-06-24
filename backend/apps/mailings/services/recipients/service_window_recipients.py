from apps.mailings.services.recipients.base import RecipientStrategy
from apps.clients.models import Client
from apps.mailings.models import Mailing
import logging
from apps.mailings.logging_utils import log_event, send_ws_event


logger = logging.getLogger(__name__)

class ServiceWindowRecipientStrategy(RecipientStrategy):
    def __init__(self, mailing: Mailing):
        super().__init__(mailing)

    def execute(self) -> int:
        """
        Стратегия для создания тикетов на сервисное окно.

        Фильтрует клиентов с тарифами Gold/Platinum, у которых установлено service_window=True.
        В будущем — отправка тикета в систему поддержки.

        Returns:
            int: Количество клиентов, для которых сгенерирована логика.
        """
        clients = Client.objects.filter(contact_status=True, service_info__service_pack__in=["gold", "platinum"])
        count = 0

        for client in clients:
            # TODO: В будущем здесь будет логика создания тикета
            logger.info(f"🛠️ Запрос сервисного окна: {client.client_name} (тариф: {client.service_info.service_pack})")
            log_event(self.mailing.id,
                "info", f"🛠️ Запрос сервисного окна: {client.client_name} (тариф: {client.service_info.service_pack})")
            send_ws_event(self.mailing.id,
                "info", {"message": f"🛠️ Запрос сервисного окна: {client.client_name} (тариф: {client.service_info.service_pack})"})
            count += 1

        return count
