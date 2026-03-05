from channels.generic.websocket import AsyncJsonWebsocketConsumer


class HolidayConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("holidays", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("holidays", self.channel_name)

    async def holiday_added(self, event):
        await self.send_json({
            "type": "holiday_added",
            "holiday": event.get("holiday"),
        })

    async def holiday_updated(self, event):
        await self.send_json({
            "type": "holiday_updated",
            "holiday": event.get("holiday"),
        })

    async def holiday_deleted(self, event):
        await self.send_json({
            "type": "holiday_deleted",
            "id": event.get("id"),
            "date": event.get("date"),
        })


class LeavesConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("leaves", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("leaves", self.channel_name)

    async def leave_added(self, event):
        await self.send_json({
            "type": "leave_added",
            "leave": event.get("leave"),
        })

    async def leave_updated(self, event):
        await self.send_json({
            "type": "leave_updated",
            "leave": event.get("leave"),
        })

    async def leave_deleted(self, event):
        await self.send_json({
            "type": "leave_deleted",
            "id": event.get("id"),
            "worker_id": event.get("worker_id"),
            "start_date": event.get("start_date"),
            "end_date": event.get("end_date"),
        })
