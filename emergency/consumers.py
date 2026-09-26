import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

logger = logging.getLogger(__name__)


class EmergencyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.emergency_id = self.scope['url_route']['kwargs']['emergency_id']
        self.room_group_name = f'emergency_{self.emergency_id}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope.get('user')

        # Feature 1 & 3: If location update is sent by an authenticated responder, log server-side breadcrumb
        if data.get('type') == 'location' and data.get('latitude') and data.get('longitude'):
            if user and user.is_authenticated:
                res = await self._record_breadcrumb(
                    user=user,
                    lat=float(data['latitude']),
                    lng=float(data['longitude']),
                    emergency_id=int(self.emergency_id)
                )
                if res and res.get('arrival_triggered'):
                    data['show_arrival_guidance'] = True
                    data['arrived'] = True

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'emergency_update',
            'data': data
        })

    async def emergency_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def _record_breadcrumb(self, user, lat, lng, emergency_id):
        try:
            from incident_records.services import IncidentRecordService
            return IncidentRecordService.record_location_breadcrumb(
                responder_user=user,
                latitude=lat,
                longitude=lng,
                emergency_id=emergency_id
            )
        except Exception as e:
            logger.error(f"[EmergencyConsumer] Breadcrumb logging error: {e}")
            return None
