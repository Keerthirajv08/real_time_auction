import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class AuctionConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'auction_{self.room_name}'
        self.user = self.scope['user']

        #print(f"DEBUG: User connected to Group: {self.room_group_name}")

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'status': 'joined',
                    'username': self.user.username
                }
            )

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        if self.user.is_authenticated:
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'status': 'left',
                    'username': self.user.username
                }
            )
    
    def auction_message(self, event):
        message = event.get('message', '')
        new_price = event['new_price']
        new_end_time = event.get('new_end_time', None)

        self.send(text_data=json.dumps({
            'message': message,
            'new_price': str(new_price),
            'new_end_time': new_end_time
        }))

    def user_status(self, event):
        self.send(text_data=json.dumps({
            'type': 'status_update',
            'username': event['username'],
            'status': event['status']
        }))

    def receive(self, text_data):
        print(f"DEBUG: Server received: {text_data}")

        text_data_json = json.loads(text_data)

        message_type = text_data_json.get('type')
        message = text_data_json.get('message')

        if message_type == 'chat_message':
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username
                }
            )
    
    def chat_message(self, event):
        message = event['message']
        username = event['username']

        self.send(text_data=json.dumps({
            'type': 'chat',
            'message': message,
            'username': username
        }))


class LobbyConsumer(WebsocketConsumer):
    def connect(self):
        self.room_group_name = 'lobby'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
    
    def lobby_update(self, event):
        self.send(text_data=json.dumps(event))

        