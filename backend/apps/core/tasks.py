from celery import shared_task

@shared_task
def test_celery_task(x, y):
    return x + y
