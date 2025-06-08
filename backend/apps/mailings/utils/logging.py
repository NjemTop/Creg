import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from apps.mailings.models import Mailing, MailingLog, LogLevel


class MailingLogHandler(logging.Handler):
    """Logging handler that stores logs in the database and sends them via WebSocket."""

    def __init__(self, mailing_id):
        super().__init__()
        self.mailing_id = mailing_id

    def emit(self, record):
        try:
            message = self.format(record)
            level = getattr(LogLevel, record.levelname.upper(), LogLevel.INFO)

            mailing = Mailing.objects.get(id=self.mailing_id)
            MailingLog.objects.create(mailing=mailing, level=level, message=message)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"mailing_{self.mailing_id}",
                {
                    "type": "mailing_update",
                    "log": {
                        "level": level,
                        "message": message,
                        "timestamp": timezone.now().isoformat(),
                    },
                },
            )
        except Exception:
            pass


def log_event(mailing_id, level, message, event_type="log"):
    """Log a mailing event, store it in the DB and broadcast via WebSocket."""
    mailing = Mailing.objects.get(id=mailing_id)

    log_methods = {
        LogLevel.INFO: logging.getLogger(__name__).info,
        LogLevel.WARNING: logging.getLogger(__name__).warning,
        LogLevel.ERROR: logging.getLogger(__name__).error,
        LogLevel.CRITICAL: logging.getLogger(__name__).critical,
    }
    log_method = log_methods.get(level, logging.getLogger(__name__).debug)
    log_method(message)

    MailingLog.objects.create(mailing=mailing, level=level, message=message)

    channel_layer = get_channel_layer()
    payload = {"type": "mailing_update"}
    if event_type == "log":
        payload["log"] = {
            "level": level,
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }
    else:
        payload[event_type] = message

    async_to_sync(channel_layer.group_send)(f"mailing_{mailing_id}", payload)
