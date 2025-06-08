import json
from channels.generic.websocket import AsyncWebsocketConsumer


class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send("✅ WebSocket connected!")

    async def receive(self, text_data):
        data = json.loads(text_data).get("message", "")
        await self.send(f"🔄 Echo: {data}")

    async def disconnect(self, close_code):
        print(f"❌ WebSocket closed: {close_code}")


class MailingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """ Подключение к WebSocket-группе рассылки """
        self.mailing_id = self.scope["url_route"]["kwargs"]["mailing_id"]
        self.group_name = f"mailing_{self.mailing_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        """ Отключение от группы WebSocket """
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def mailing_update(self, event):
        """ Отправка обновления статуса или логов """
        data = {}

        if "status" in event:
            data["status"] = event["status"]
        if "error" in event:
            data["error"] = event["error"]
        if "log" in event:
            data["log"] = event["log"]
        if "recipient" in event:
            data["recipient"] = event["recipient"]
        if "completed_at" in event:
            data["completed_at"] = event["completed_at"]

        if data:
            await self.send(text_data=json.dumps(data))
