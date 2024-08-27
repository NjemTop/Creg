from celery import shared_task
from scripts.jfrog.artifactory_downloads_log.monitor_log import analyze_logs_and_get_data
import logging
from django.core.mail import EmailMessage
from scripts.email.settings import set_email_config
from django.conf import settings

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def analyze_logs_task(self):
    try:
        status, client_data = analyze_logs_and_get_data()
        if status != "Успешно":
            raise Exception(f"Ошибка анализа логов: {status}")
        return {'status': 'SUCCESS', 'client_data': client_data}
    except Exception as e:
        self.update_state(state='FAILURE', meta={'exc_message': str(e)})
        logger.error(f"Ошибка выполнения задачи analyze_logs_task: {str(e)}")
        raise


@shared_task
def echo(x, y):
    return x + y


@shared_task
def send_test_email(email):
    try:
        # Устанавливаем конфигурацию для продовской почты
        set_email_config('internal')

        email = EmailMessage(
            'Test Email',
            'This is a test email.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
        )
        email.send()
        return "Email sent successfully"
    except Exception as error_message:
        return str(error_message)
