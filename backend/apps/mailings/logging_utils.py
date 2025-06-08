import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import Mailing, MailingLog, LogLevel


class MailLogHandler(logging.Handler):
    """Logging handler that writes mailing logs to DB and WebSocket."""
    def __init__(self, mailing_id):
        super().__init__()
        self.mailing_id = mailing_id

    def emit(self, record):
        message = self.format(record)
        level_map = {
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARNING,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.CRITICAL,
        }
        level = level_map.get(record.levelno, LogLevel.INFO)

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


def send_ws_event(mailing_id, event_type, message):
    """Send an event to the WebSocket group for a mailing."""
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"mailing_{mailing_id}",
        {
            "type": "mailing_update",
            event_type: message,
        },
    )


def log_event(mailing_id, level, message):
    """Log a message using the MailLogHandler interface."""
    logger = get_mailing_logger(mailing_id)
    log_methods = {
        LogLevel.INFO: logger.info,
        LogLevel.WARNING: logger.warning,
        LogLevel.ERROR: logger.error,
        LogLevel.CRITICAL: logger.critical,
    }
    log_method = log_methods.get(level, logger.info)
    log_method(message)


def get_mailing_logger(mailing_id, name=None):
    """Return a logger configured with a MailLogHandler."""
    logger_name = name or f"mailing_{mailing_id}"
    logger = logging.getLogger(logger_name)
    if not any(
        isinstance(h, MailLogHandler) and h.mailing_id == mailing_id
        for h in logger.handlers
    ):
        logger.addHandler(MailLogHandler(mailing_id))
    logger.setLevel(logging.INFO)
    return logger
