import json

from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active_users = set()
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = "chat_%s" % self.room_name

        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        self.active_users = []
        self.active_user_channels = []
        self.active_users.append(self.channel_name)
        self.active_user_channels.append(
            self.channel_name)
        await self.accept()
        await self.send_active_users_count()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        self.active_users.remove(self.channel_name)
        self.active_user_channels.remove(
            self.channel_name)
        await self.send_active_users_count()

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        data = text_data or bytes_data
        text_data_json = json.loads(data)
        message = text_data_json["message"]
        name = text_data_json["name"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat_message", "message": message, "name": name}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        name = event["name"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message, "name": name}))

        active_users_count = len(self.active_users)

        for user_channel in self.active_users:
            await self.channel_layer.send(
                user_channel,
                {
                    "type": "update_active_users_count",
                    "active_users_count": active_users_count,
                }
            )

    async def send_active_users_count(self):
        active_users_count = len(self.active_users)
        for user_channel in self.active_user_channels:
            await self.channel_layer.send(
                user_channel,
                {
                    "type": "update_active_users_count",
                    "active_users_count": active_users_count,
                }
            )

    async def update_active_users_count(self, event):
        active_users_count = event["active_users_count"]

        await self.send(text_data=json.dumps({"active_users": active_users_count}))