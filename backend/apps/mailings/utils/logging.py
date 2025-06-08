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
