import json
from channels.generic.websocket import AsyncWebsocketConsumer

class LobbyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'lobby_{self.room_code}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Currently not expecting to receive data from clients
        pass

    async def send_player_list(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_list',
            'players': event['players'],
        }))

    async def game_started(self, event):
        player_id = event.get('player_id')
        role = event.get('role')

        await self.send(text_data=json.dumps({
            'type': 'game_started',
            'player_id': player_id,
            'role': role,
        }))


class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f"game_{self.room_code}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        # (Optional, only if you're sending messages from client)
        pass

    async def game_over(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_over',
            'players': event['players']
        }))