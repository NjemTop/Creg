import traceback
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from apps.mailings.services.base.email_sender import EmailSender
from apps.mailings.services.recipients import get_recipient_strategy
from apps.mailings.logging_utils import send_ws_event, log_event, get_mailing_logger
from apps.mailings.models import Mailing, MailingRecipient, MailingTestRecipient, MailingStatus, RecipientStatus, MailingMode


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
            strategy = get_recipient_strategy(mailing)
            log_event(mailing.id, "debug", f"🔁 Выбрана стратегия получателей: {strategy.__class__.__name__}")
            send_ws_event(mailing.id, "info", {"message": f"Стратегия: {strategy.__class__.__name__}"})
            strategy.execute()
            recipients = MailingRecipient.objects.filter(mailing=mailing, status=RecipientStatus.PENDING)

        if not recipients.exists():
            error_msg = f"⚠️ [{self.request.id}] Рассылка {mailing.id} прервана: Нет получателей."
            raise RuntimeError(error_msg)

        success_count = 0
        error_count = 0

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
                    mailing_id=mailing.id,
                )
                sender.logger = mail_logger
                sender.error_logger = mail_logger
                try:
                    sender.send_email()
                except ValueError as smtp_error:
                    error_msg = f"🚨 [{self.request.id}] SMTP не настроен: {smtp_error}"
                    log_event(mailing.id, "critical", error_msg)
                    send_ws_event(mailing.id, "error", {"message": error_msg})
                    raise RuntimeError(error_msg)
                except Exception as send_error:
                    error_msg = f"❌ [{self.request.id}] Ошибка отправки письма: {send_error}"
                    log_event(mailing.id, "error", error_msg)
                    send_ws_event(mailing.id, "error", {"message": error_msg})
                    raise


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

        mail_logger = get_mailing_logger(mailing_id)
        log_event(mailing_id, "critical", error_msg)
        send_ws_event(mailing_id, "error", {"message": error_msg})

        try:
            mailing = Mailing.objects.get(id=mailing_id)
            mailing.status = MailingStatus.FAILED
            mailing.completed_at = timezone.now()
            mailing.error_message = error_msg
            mailing.save()

            send_ws_event(mailing_id, "status", {"code": mailing.status, "display": mailing.get_status_display()})
            send_ws_event(mailing_id, "completed_at", timezone.localtime(mailing.completed_at).isoformat())
        except Exception:
            pass

        self.update_state(
            state="FAILURE",
            meta={
                "task_name": self.name,
                "error": error_msg,
                "worker": self.request.hostname,
                "traceback": error_traceback,
            }
        )

        raise
