from channels.generic.websocket import AsyncJsonWebsocketConsumer


class BlogConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("blogs", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("blogs", self.channel_name)

    async def blog_added(self, event):
        await self.send_json(event)

    async def blog_updated(self, event):
        await self.send_json(event)

    async def blog_deleted(self, event):
        await self.send_json(event)


class CategoryConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("categories", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("categories", self.channel_name)

    async def category_added(self, event):
        await self.send_json(event)

    async def category_updated(self, event):
        await self.send_json(event)

    async def category_deleted(self, event):
        await self.send_json(event)


class InventoryConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("inventory", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("inventory", self.channel_name)

    async def inventory_added(self, event):
        await self.send_json(event)

    async def inventory_updated(self, event):
        await self.send_json(event)

    async def inventory_deleted(self, event):
        await self.send_json(event)


class OrderConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("orders", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("orders", self.channel_name)

    async def order_added(self, event):
        await self.send_json(event)

    async def order_updated(self, event):
        await self.send_json(event)

    async def order_deleted(self, event):
        await self.send_json(event)
