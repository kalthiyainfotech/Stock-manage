from channels.generic.websocket import AsyncJsonWebsocketConsumer

class BlogConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("blogs", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("blogs", self.channel_name)

    async def blog_added(self, event):
        await self.send_json({
            "type": "blog_added",
            "blog": event["blog"],
        })

    async def blog_updated(self, event):
        await self.send_json({
            "type": "blog_updated",
            "blog": event["blog"],
        })

    async def blog_deleted(self, event):
        await self.send_json({
            "type": "blog_deleted",
            "id": event["id"],
        })
