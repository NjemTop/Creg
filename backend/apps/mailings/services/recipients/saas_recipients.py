from apps.mailings.services.recipients.base import RecipientStrategy
from apps.clients.models import Client
from apps.mailings.models import Mailing
import logging
from apps.mailings.logging_utils import log_event, send_ws_event


logger = logging.getLogger(__name__)

class SaaSRecipientStrategy(RecipientStrategy):
    def execute(self):
        """
        Обрабатывает рассылку с отметкой "SaaS-уведомление".

        Фильтрует клиентов с флагом `saas=True`. Пока что только логирует, 
        но в будущем здесь будет логика создания тикетов или отправки уведомлений.

        Returns:
            int: Количество клиентов SaaS, которым должна быть отправлена рассылка.
        """
        clients = Client.objects.filter(contact_status=True, saas=True)
        count = clients.count()

        for client in clients:
            # TODO: В будущем здесь будет логика создания тикета - create_ticket()
            logger.info(f"[SaaS] Клиент {client.client_name} отправлено уведомление. Планируемое время обновления: {self.mailing.saas_update_time}")
            log_event(self.mailing.id,
                "info", f"[SaaS] Клиент {client.client_name} отправлено уведомление. Планируемое время обновления: {self.mailing.saas_update_time}")
            send_ws_event(self.mailing.id,
                "info", {"message": f"🛠️ [SaaS] Клиент {client.client_name} отправлено уведомление. Планируемое время обновления: {self.mailing.saas_update_time}"})

        self.mailing.recipients_generated = True
        self.mailing.save()
        return count
