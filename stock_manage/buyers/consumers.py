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


class CategoryConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("categories", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("categories", self.channel_name)

    async def category_added(self, event):
        await self.send_json({
            "type": "category_added",
            "category": event["category"],
        })

    async def category_updated(self, event):
        await self.send_json({
            "type": "category_updated",
            "category": event["category"],
        })

    async def category_deleted(self, event):
        await self.send_json({
            "type": "category_deleted",
            "id": event["id"],
        })


class InventoryConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("inventory", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("inventory", self.channel_name)

    async def inventory_added(self, event):
        await self.send_json({
            "type": "inventory_added",
            "inventory": event.get("inventory"),
        })

    async def inventory_updated(self, event):
        await self.send_json({
            "type": "inventory_updated",
            "inventory": event.get("inventory"),
        })

    async def inventory_deleted(self, event):
        await self.send_json({
            "type": "inventory_deleted",
            "id": event.get("id"),
        })
