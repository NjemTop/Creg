import logging
import smtplib
import traceback
from celery import shared_task
from django.core.mail.backends.smtp import EmailBackend
from django.db import transaction
from django.utils import timezone
from apps.mailings.services.base.email_sender import EmailSender
from apps.mailings.utils.logging import MailingLogHandler, log_event
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




@shared_task(bind=True)
def send_mailing_task(self, mailing_id):
    """Фоновая отправка рассылки клиентам с кастомным SMTP"""
    handler = None
    try:
        mailing = Mailing.objects.get(id=mailing_id)

        handler = MailingLogHandler(mailing.id)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(handler)

        mailing.status = MailingStatus.IN_PROGRESS
        mailing.started_at = timezone.now()
        mailing.save()

        log_event(
            mailing.id,
            "info",
            mailing.get_status_display(),
            event_type="status",
        )
        log_event(
            mailing.id,
            "info",
            f"📨 [{self.request.id}] Рассылка запущена (Режим: {mailing.mode}, Язык: {mailing.language}).",
        )

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

            log_event(
                mailing.id,
                "info",
                mailing.get_status_display(),
                event_type="status",
            )
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

            log_event(
                mailing.id,
                "info",
                mailing.get_status_display(),
                event_type="status",
            )
            log_event(mailing.id, "error", error_msg)

            raise

        success_count = 0
        error_count = 0

        smtp_config = {
            "SMTP": email_backend.host,
            "USER": email_backend.username or "",
            "PASSWORD": email_backend.password or "",
            "FROM": email_backend.username or "noreply@example.com",
        }

        for recipient in recipients:
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
                sender.config.update({
                    "MAIL_SETTINGS": smtp_config,
                    "MAIL_SETTINGS_SUPPORT": smtp_config,
                })
                sender.send_email()

                recipient.status = RecipientStatus.SENT
                recipient.sent_at = timezone.now()
                recipient.error_message = ""
                success_count += 1

            except Exception as error:
                recipient.status = RecipientStatus.ERROR
                error_msg = f"⚠️ [{self.request.id}] Ошибка отправки на {recipient.email}: {str(error)}"
                recipient.error_message = error_msg
                error_count += 1
                log_event(mailing.id, "error", error_msg)

            recipient.save()

        log_event(
            mailing.id,
            "info",
            mailing.get_status_display(),
            event_type="status",
        )

        # Итоговый статус рассылки
        with transaction.atomic():
            mailing.completed_at = timezone.now()
            mailing.status = MailingStatus.FAILED if error_count > 0 else MailingStatus.COMPLETED
            mailing.save()
        
        log_event(mailing.id, "info", f"✅ Рассылка завершена: {success_count} отправлено, {error_count} с ошибками.")

        log_event(
            mailing.id,
            "info",
            mailing.get_status_display(),
            event_type="status",
        )

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

            log_event(
                mailing.id,
                "info",
                mailing.get_status_display(),
                event_type="status",
            )
            log_event(mailing_id, "critical", error_msg)

        raise
    finally:
        if handler:
            logging.getLogger().removeHandler(handler)
