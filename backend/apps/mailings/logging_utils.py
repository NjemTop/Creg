import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from .models import Mailing, MailingLog, LogLevel
from collections import deque


class MailLogHandler(logging.Handler):
    """Обработчик логов, который записывает почтовые логи в базу данных
    и отправляет в WebSocket с фильтрацией повторов.

    Особенности:
    - Записывает сообщения логов в таблицу MailingLog.
    - Отправляет сообщения в WebSocket-группу рассылки (mailing_<id>).
    - Фильтрует повторы: одинаковое сообщение не будет записано повторно, если оно было среди последних `history_size`.
    """
    def __init__(self, mailing_id, history_size=10):
        """
        Args:
            mailing_id (int): Идентификатор рассылки.
            history_size (int): Максимальное количество последних сообщений для фильтрации повторов.
        """
        super().__init__()
        self.mailing_id = mailing_id
        # Кешируем последние сообщения
        self.last_messages = deque(maxlen=history_size)

    def emit(self, record):
        """
        Обрабатывает лог-запись:
        - Если сообщение уже было недавно — игнорируется.
        - Иначе записывается в базу (MailingLog) и отправляется по WebSocket.

        Args:
            record (LogRecord): Запись логгера.
        """
        message = self.format(record).strip()
        if message in self.last_messages:
            return  # пропускаем повтор
        self.last_messages.append(message)

        level_map = {
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARNING,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.CRITICAL,
        }
        level = level_map.get(record.levelno, LogLevel.INFO)

        # Повторно получаем объект рассылки
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
    """Отправляет произвольное событие в WebSocket-группу рассылки.

    Args:
        mailing_id (int): ID рассылки.
        event_type (str): Тип события (например, 'status', 'error', 'recipient').
        message (dict): Данные события, передаваемые на клиент.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"mailing_{mailing_id}",
        {
            "type": "mailing_update",
            event_type: message,
        },
    )


def log_event(mailing_id, level, message):
    """Логирует сообщение через MailLogHandler (и, как следствие, в БД и WebSocket).

    Args:
        mailing_id (int): ID рассылки.
        level (int): Уровень лога (LogLevel.INFO и т.п.).
        message (str): Сообщение лога.
    """
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
    """Возвращает и настраивает логгер, связанный с MailLogHandler.

    Args:
        mailing_id (int): ID рассылки.
        name (str, optional): Имя логгера. По умолчанию формируется из mailing_id.

    Returns:
        logging.Logger: Логгер, настроенный с MailLogHandler.
    """
    logger_name = name or f"mailing_{mailing_id}"
    logger = logging.getLogger(logger_name)
    if not any(
        isinstance(h, MailLogHandler) and h.mailing_id == mailing_id
        for h in logger.handlers
    ):
        logger.addHandler(MailLogHandler(mailing_id))
    logger.setLevel(logging.INFO)
    return logger
