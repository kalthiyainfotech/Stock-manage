from channels.generic.websocket import AsyncJsonWebsocketConsumer

class DashboardConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Authenticate if necessary (e.g., self.scope["user"].is_staff)
        await self.channel_layer.group_add("dashboard", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard", self.channel_name)

    async def dashboard_update(self, event):
        await self.send_json({
            "type": "dashboard_update",
            "data": event["data"],
        })
