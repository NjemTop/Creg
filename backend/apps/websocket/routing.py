from django.urls import re_path
from .consumers import EchoConsumer, MailingConsumer

websocket_urlpatterns = [
    re_path(r"ws/test-echo/$", EchoConsumer.as_asgi()),
    re_path(r"ws/mailing/(?P<mailing_id>\d+)/$", MailingConsumer.as_asgi()),
]
