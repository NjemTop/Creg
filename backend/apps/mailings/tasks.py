import logging
import traceback
from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import (
    Mailing,
    MailingLog,
    MailingRecipient,
    MailingTestRecipient,
    MailingStatus,
    RecipientStatus,
    MailingMode,
    LogLevel,
)
from apps.mailings.services.runners.send_test_email import send_test_email
from apps.mailings.services.runners.send_mailing import send_mailing


logger = logging.getLogger(__name__)

def send_ws_event(mailing_id, event_type, message):
    """ Универсальная функция отправки событий в WebSocket """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"mailing_{mailing_id}",
        {
            "type": "mailing_update",
            event_type: message
        }
    )

def log_event(mailing_id, level, message):
    """ Универсальная функция логирования (Logger + БД + WebSocket) """
    mailing = Mailing.objects.get(id=mailing_id)

    # Записываем в Django Logger
    log_methods = {
        LogLevel.INFO: logger.info,
        LogLevel.WARNING: logger.warning,
        LogLevel.ERROR: logger.error,
        LogLevel.CRITICAL: logger.critical
    }
    log_method = log_methods.get(level, logger.debug)
    log_method(message)

    # Записываем в БД
    MailingLog.objects.create(mailing=mailing, level=level, message=message)

    # Отправляем WebSocket-событие
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"mailing_{mailing_id}",
        {
            "type": "mailing_update",
            "log": {
                "level": level,
                "message": message,
                "timestamp": timezone.now().isoformat()
            }
        }
    )


@shared_task(bind=True)
def send_mailing_task(self, mailing_id):
    """Фоновая отправка рассылки клиентам с кастомным SMTP"""
    try:
        mailing = Mailing.objects.get(id=mailing_id)
        mailing.status = MailingStatus.IN_PROGRESS
        mailing.started_at = timezone.now()
        mailing.save()

        send_ws_event(mailing.id, "status", mailing.get_status_display())
        log_event(mailing.id, "info", f"📨 [{self.request.id}] Рассылка запущена (Режим: {mailing.mode}, Язык: {mailing.language}).")

        if mailing.mode == MailingMode.TEST:
            emails = list(mailing.test_recipients.values_list("email", flat=True))
            if not emails:
                raise ValueError("Нет тестовых получателей")
            send_test_email(
                emails=emails,
                mailing_type="standard_mailing",
                release_type=mailing.release_type,
                server_version=mailing.server_version or None,
                ipad_version=mailing.ipad_version or None,
                android_version=mailing.android_version or None,
                language=mailing.language.code if mailing.language else "ru",
            )
            mailing.test_recipients.update(
                status=RecipientStatus.SENT,
                sent_at=timezone.now(),
                error_message="",
            )
        else:
            send_mailing(
                mailing_type="standard_mailing",
                release_type=mailing.release_type,
                server_version=mailing.server_version or None,
                ipad_version=mailing.ipad_version or None,
                android_version=mailing.android_version or None,
            )
            mailing.recipients.update(
                status=RecipientStatus.SENT,
                sent_at=timezone.now(),
                error_message="",
            )
        mailing.completed_at = timezone.now()
        mailing.status = MailingStatus.COMPLETED
        mailing.save()
        log_event(mailing.id, "info", "✅ Рассылка завершена")
        send_ws_event(mailing.id, "status", mailing.get_status_display())

    except Exception as error:
        error_msg = f"❌ [{self.request.id}] Критическая ошибка: {str(error)}"
        error_traceback = traceback.format_exc()

        if not isinstance(error, ValueError):
            logger.critical(error_msg, exc_info=True)

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

            send_ws_event(mailing.id, "status", mailing.get_status_display())
            log_event(mailing_id, "critical", error_msg)

        raise
