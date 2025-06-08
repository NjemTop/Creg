import logging
import smtplib
import traceback
from celery import shared_task
from django.core.mail import send_mail
from django.core.mail.backends.smtp import EmailBackend
from django.db import transaction
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Mailing, MailingLog, MailingRecipient, MailingTestRecipient, MailingStatus, RecipientStatus, MailingMode, LogLevel
from apps.configurations.models import SMTPSettings


logger = logging.getLogger(__name__)

def get_smtp_backend():
    """Получаем настройки SMTP из базы и создаём EmailBackend"""
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

        # Определяем список получателей (тест или прод)
        recipients = (
            MailingTestRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)
            if mailing.mode == MailingMode.TEST
            else MailingRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)
        )

        if not recipients.exists():
            error_msg = f"⚠️ [{self.request.id}] Рассылка {mailing.id} прервана: Нет получателей."
            logger.warning(error_msg)
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
                    "traceback": None,
                }
            )

            send_ws_event(mailing.id, "status", mailing.get_status_display())
            log_event(mailing.id, "error", error_msg)

            raise

        try:
            email_backend = get_smtp_backend()
        except ValueError as error:
            error_msg = f"🚨 [{self.request.id}] Ошибка SMTP: {str(error)}"
            logger.error(error_msg)
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
                    "traceback": None,
                }
            )

            send_ws_event(mailing.id, "status", mailing.get_status_display())
            log_event(mailing.id, "error", error_msg)

            raise

        LANG_MESSAGES = {
            "ru": {
                "subject": f"Обновление {mailing.server_version}",
                "message": f"Версия сервера: {mailing.server_version}\nВерсия iPad: {mailing.ipad_version}\nВерсия Android: {mailing.android_version}",
            },
            "en": {
                "subject": f"Update {mailing.server_version}",
                "message": f"Server Version: {mailing.server_version}\n iPad Version: {mailing.ipad_version}\n Android Version: {mailing.android_version}",
            },
        }

        success_count = 0
        error_count = 0

        for recipient in recipients:
            try:
                lang = mailing.language.code if mailing.mode == MailingMode.TEST else (recipient.client.language.code if recipient.client else 'ru')
                email_content = LANG_MESSAGES.get(lang, LANG_MESSAGES["ru"])  # Если язык не найден, по умолчанию "ru"

                send_mail(
                    subject=email_content["subject"],
                    message=email_content["message"],
                    from_email=email_backend.username,
                    recipient_list=[recipient.email],
                    connection=email_backend,
                    fail_silently=True
                )

                recipient.status = RecipientStatus.SENT
                recipient.sent_at = timezone.now()
                recipient.error_message = ''
                success_count += 1

            except smtplib.SMTPException as smtp_error:
                recipient.status = RecipientStatus.ERROR
                error_msg = f"❌ [{self.request.id}] Ошибка SMTP при отправке {recipient.email}: {str(smtp_error)}"
                recipient.error_message = error_msg
                error_count += 1
                logger.error(error_msg)
                log_event(mailing.id, "error", error_msg)

            except Exception as error:
                recipient.status = RecipientStatus.ERROR
                error_msg = f"⚠️ [{self.request.id}] Ошибка отправки на {recipient.email}: {str(error)}"
                recipient.error_message = error_msg
                error_count += 1
                log_event(mailing.id, "error", error_msg)

            recipient.save()

            send_ws_event(mailing.id, "status", mailing.get_status_display())

        # Итоговый статус рассылки
        with transaction.atomic():
            mailing.completed_at = timezone.now()
            mailing.status = MailingStatus.FAILED if error_count > 0 else MailingStatus.COMPLETED
            mailing.save()
        
        log_event(mailing.id, "info", f"✅ Рассылка завершена: {success_count} отправлено, {error_count} с ошибками.")

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
