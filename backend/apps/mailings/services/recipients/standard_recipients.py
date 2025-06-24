from apps.mailings.services.recipients.base import RecipientStrategy
from apps.clients.models import Client
from apps.mailings.models import Mailing, MailingRecipient


class StandardRecipientStrategy(RecipientStrategy):
    def __init__(self, mailing: Mailing):
        self.mailing = mailing

    def execute(self):
        """
        Генерирует список получателей для прод-режима рассылки на основе данных клиентов.

        Функция выполняет:
        - фильтрацию активных клиентов (`contact_status=True`);
        - отбор по типу релиза (2.x или 3.x версия);
        - выбор контактов с включённым флагом `notification_update=True`;
        - создание записей в таблице MailingRecipient для каждого email с указанием языка.

        Returns:
            int: Количество сгенерированных получателей.
        """

        # Выбираем клиентов с активным статусом и тех.инфой
        clients = Client.objects.filter(contact_status=True).select_related("technical_info")

        # Фильтрация по типу релиза
        if self.mailing.release_type == "release3x":
            clients = clients.filter(technical_info__server_version__startswith="3.")
        elif self.mailing.release_type == "release2x":
            clients = clients.filter(technical_info__server_version__startswith="2.")

        count = 0
        for client in clients:
            lang = client.language.code if client.language else 'ru'  # fallback
            contacts = client.contacts.filter(notification_update=True)

            for contact in contacts:
                MailingRecipient.objects.create(
                    mailing=self.mailing,
                    client=client,
                    email=contact.email,
                    language=lang,
                )
                count += 1

        self.mailing.recipients_generated = True
        self.mailing.save()
        return count
