import logging
import traceback
from celery import shared_task
from django.core.mail.backends.smtp import EmailBackend
from django.db import transaction
from django.utils import timezone
from apps.mailings.services.base.email_sender import EmailSender
from .logging_utils import send_ws_event, log_event, get_mailing_logger
from .models import Mailing, MailingRecipient, MailingTestRecipient, MailingStatus, RecipientStatus, MailingMode
from apps.clients.models import Client
from apps.configurations.models import SMTPSettings

def get_smtp_backend():
    """Возвращает EmailBackend на основе активных настроек SMTP.

    Выбирает первую включённую запись в таблице ``SMTPSettings`` и
    инициализирует объект :class:`EmailBackend`. Если активной
    конфигурации нет, возбуждает ``ValueError``.
    """
    smtp = SMTPSettings.objects.filter(enabled=True).first()

    if not smtp:
        raise ValueError("SMTP-отправка отключена. Включите её в настройках.")

    return EmailBackend(
        host=smtp.smtp_host,
        port=smtp.smtp_port,
        username=smtp.smtp_user,
        password=smtp.smtp_password,
        use_tls=smtp.use_tls,
        use_ssl=smtp.use_ssl,
        fail_silently=False
    )


def populate_prod_recipients(mailing):
    """Создаёт получателей для продакшен-рассылки.

    Если у рассылки нет получателей, метод подберёт всех активных клиентов,
    подходящих по языку, и создаст записи :class:`MailingRecipient` для каждого
    контакта с разрешёнными уведомлениями.

    Args:
        mailing (:class:`Mailing`): Объект рассылки, для которого формируются
            получатели.

    Returns:
        int: Количество созданных получателей.
    """
    clients = Client.objects.filter(contact_status=True)
    if mailing.language:
        clients = clients.filter(language=mailing.language)

    created = 0
    for client in clients:
        for contact in client.contacts.filter(notification_update=True):
            MailingRecipient.objects.create(
                mailing=mailing,
                client=client,
                email=contact.email,
            )
            created += 1
    return created


@shared_task(bind=True)
def send_mailing_task(self, mailing_id):
    """Отправляет рассылку в фоновом режиме.

    Задача Celery, которая формирует список получателей, подготавливает
    SMTP-соединение и отправляет письма. В процессе работы отправляет
    события по WebSocket и пишет логи в базу данных.

    Args:
        mailing_id (int): Идентификатор рассылки.

    Raises:
        RuntimeError: Если не найдено активных получателей или отсутствует
            валидная SMTP-конфигурация.
    """
    try:
        mailing = Mailing.objects.get(id=mailing_id)
        mail_logger = get_mailing_logger(mailing.id)
        mailing.status = MailingStatus.IN_PROGRESS
        mailing.started_at = timezone.now()
        mailing.save()

        send_ws_event(
            mailing.id,
            "status",
            {"code": mailing.status, "display": mailing.get_status_display()},
        )
        log_event(mailing.id, "info", f"📨 [{self.request.id}] Рассылка запущена (Режим: {mailing.mode}, Язык: {mailing.language}).")

        # Определяем список получателей (тест или прод)
        recipients = (
            MailingTestRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)
            if mailing.mode == MailingMode.TEST
            else MailingRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)
        )

        if not recipients.exists() and mailing.mode == MailingMode.PROD:
            populate_prod_recipients(mailing)
            recipients = MailingRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)

        if not recipients.exists():
            error_msg = f"⚠️ [{self.request.id}] Рассылка {mailing.id} прервана: Нет получателей."
            raise RuntimeError(error_msg)

        try:
            email_backend = get_smtp_backend()
        except ValueError as error:
            error_msg = f"🚨 [{self.request.id}] Ошибка SMTP: {str(error)}"
            raise RuntimeError(error_msg)

        success_count = 0
        error_count = 0

        smtp_config = {
            "SMTP": email_backend.host,
            "USER": email_backend.username or "",
            "PASSWORD": email_backend.password or "",
            "FROM": email_backend.username or "noreply@example.com",
        }

        for recipient in recipients:
            client_name = (
                recipient.client.client_name
                if getattr(recipient, "client", None)
                else "Тестовый получатель"
            )
            try:
                lang = mailing.language.code if mailing.mode == MailingMode.TEST else (
                    recipient.client.language.code if recipient.client and recipient.client.language else "ru"
                )

                sender = EmailSender(
                    emails=[recipient.email],
                    mailing_type="standard_mailing",
                    release_type=mailing.release_type,
                    server_version=mailing.server_version,
                    ipad_version=mailing.ipad_version,
                    android_version=mailing.android_version,
                    language=lang,
                )
                sender.logger = mail_logger
                sender.error_logger = mail_logger
                sender.config.update({
                    "MAIL_SETTINGS": smtp_config,
                    "MAIL_SETTINGS_SUPPORT": smtp_config,
                })
                sender.send_email()

                recipient.status = RecipientStatus.SENT
                recipient.sent_at = timezone.now()
                recipient.error_message = ""
                success_count += 1
                log_event(
                    mailing.id,
                    "info",
                    f"📤 [{self.request.id}] Отправлено клиенту {client_name} <{recipient.email}>",
                )

            except Exception as error:
                recipient.status = RecipientStatus.ERROR
                error_msg = (
                    f"⚠️ [{self.request.id}] Ошибка отправки клиенту {client_name} <{recipient.email}>: {str(error)}"
                )
                recipient.error_message = error_msg
                error_count += 1
                log_event(mailing.id, "error", error_msg)

            recipient.save()

            send_ws_event(
                mailing.id,
                "recipient",
                {
                    "id": recipient.id,
                    "status": recipient.get_status_display(),
                    "status_code": recipient.status,
                },
            )

            send_ws_event(
                mailing.id,
                "status",
                {"code": mailing.status, "display": mailing.get_status_display()},
            )

        # Итоговый статус рассылки
        with transaction.atomic():
            mailing.completed_at = timezone.now()
            mailing.status = MailingStatus.FAILED if error_count > 0 else MailingStatus.COMPLETED
            mailing.save()
        
        log_event(
            mailing.id,
            "info",
            f"✅ Рассылка завершена: {success_count} отправлено, {error_count} с ошибками.",
        )

        send_ws_event(
            mailing.id,
            "status",
            {"code": mailing.status, "display": mailing.get_status_display()},
        )
        send_ws_event(
            mailing.id,
            "completed_at",
            timezone.localtime(mailing.completed_at).isoformat(),
        )

    except Exception as error:
        error_msg = f"❌ [{self.request.id}] Критическая ошибка: {str(error)}"
        error_traceback = traceback.format_exc()

        if not isinstance(error, ValueError):
            mail_logger.critical(error_msg, exc_info=True)

            mailing.status = MailingStatus.FAILED
            mailing.completed_at = timezone.now()
            mailing.error_message = error_msg
            mailing.save()

            self.update_state(
                state="FAILURE",
                meta={
                    "task_name": self.name,
                    "error": error_msg,
                    "worker": self.request.hostname,
                    "traceback": error_traceback,
                }
            )

            send_ws_event(
                mailing.id,
                "status",
                {"code": mailing.status, "display": mailing.get_status_display()},
            )
            send_ws_event(
                mailing.id,
                "completed_at",
                timezone.localtime(mailing.completed_at).isoformat(),
            )
            log_event(mailing_id, "critical", error_msg)

        raise
