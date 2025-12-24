import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


class AuctionConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'auction_{self.room_name}'

        print(f"DEBUG: User connected to Group: {self.room_group_name}")

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
    
    def auction_message(self, event):
        message = event['message']
        new_price = event['new_price']

        self.send(text_data=json.dumps({
            'message': message,
            'new_price': str(new_price)
        }))

        