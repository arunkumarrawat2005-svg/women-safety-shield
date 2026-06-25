import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room_group_name = f'location_{self.user.id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data.get('latitude')
        lng = data.get('longitude')
        emergency_id = data.get('emergency_id')

        if lat and lng:
            await self.save_location(lat, lng, emergency_id)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'location_update',
                'latitude': lat,
                'longitude': lng,
                'user_id': self.user.id,
                'username': self.user.username,
            })

    async def location_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_location(self, lat, lng, emergency_id=None):
        from tracking.models import Location
        from emergency.models import Emergency
        emergency = None
        if emergency_id:
            try:
                emergency = Emergency.objects.get(id=emergency_id)
            except Emergency.DoesNotExist:
                pass
        Location.objects.create(
            user=self.user,
            latitude=lat,
            longitude=lng,
            emergency=emergency
        )
