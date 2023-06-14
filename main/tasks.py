from celery import shared_task
from django.core.mail import EmailMessage

@shared_task
def send_test_email(email):
    try:
        email = EmailMessage(
            'Test Email',
            'This is a test email.',
            'sup-smtp@boardmaps.ru',
            [email],
        )
        email.send()
        return "Email sent successfully"
    except Exception as error_message:
        return str(error_message)


@shared_task
def echo(x, y):
    return x + y