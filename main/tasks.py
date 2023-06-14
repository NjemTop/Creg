from celery import shared_task

@shared_task(bind=True)
def echo(self, message="Hello, World!"):
    return message
