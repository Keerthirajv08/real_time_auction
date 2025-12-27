import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
import asyncio
from decimal import Decimal
from django.core.cache import cache
from django.utils import timezone
from .services import BidService
from .models import Auction, Bid
from .serializers import serialize_auction


class AuctionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'auction_{self.room_name}'
        self.user = self.scope['user']
        
        # Join auction group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()

        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'status': 'joined',
                    'username': self.user.username
                }
            )
        
        # Send current auction state on connect
        try:
            auction_data = await self.get_auction_state()
            await self.send(text_data=json.dumps({
                'type': 'connection_established',
                'auction': auction_data,
                'server_time': timezone.now().isoformat()
            }))
        except Exception:
            await self.close()
            return

        # Track active connection
        await self.track_connection(True)

    async def disconnect(self, close_code):
        await self.track_connection(False)
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'status': 'left',
                    'username': self.user.username
                }
            )

    async def auction_message(self, event):
        message = event.get('message', '')
        new_price = event.get('new_price')
        new_end_time = event.get('new_end_time')

        await self.send(text_data=json.dumps({
            'message': message,
            'new_price': str(new_price) if new_price else None,
            'new_end_time': new_end_time
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'status_update',
            'status': event['status'],
            'username': event['username']
        }))       

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        message = data.get('message')
            
        '''if message_type == 'chat_message':
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': timezone.now().isoformat()
            }))
        
        elif message_type == 'place_bid':
            await self.handle_bid(data)
        
        elif message_type == 'sync_request':
            auction_data = await self.get_auction_state()
            await self.send(text_data=json.dumps({
                'type': 'sync_response',
                'auction': auction_data
            }))'''
        
        if message_type == 'chat_message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'username': self.user.username if self.user.is_authenticated else 'Guest'
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'username': event['username']
        }))

    async def handle_bid(self, data):
        if not self.user.is_authenticated:
            await self.send(text_data=json.dumps({
                'type': 'bid_error',
                'error': 'Authentication required'
            }))
            return

        try:
            amount = Decimal(str(data['amount']))
            # Get IP from scope (requires Nginx/Daphne setup to be accurate)
            client_ip = self.scope.get('client', ['0.0.0.0'])[0]
            
            # Place bid via service
            bid, auction = await database_sync_to_async(BidService.place_bid)(
                self.room_name,
                self.user,
                amount,
                client_ip
            )
            
            # Broadcast to all in group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'bid_placed_event',
                    'bid_id': bid.id,
                    'amount': str(bid.amount),
                    'user': bid.user.username,
                    'timestamp': bid.timestamp.isoformat(),
                    'auction_version': auction.version
                }
            )
            
            # Send confirmation to bidder
            await self.send(text_data=json.dumps({
                'type': 'bid_confirmed',
                'bid_id': bid.id,
                'amount': str(bid.amount)
            }))
            
        except Exception as e:
            # Handle ValidationErrors and others
            error_msg = str(e)
            if hasattr(e, 'message'):
                error_msg = e.message
            elif hasattr(e, 'messages'):
                error_msg = ", ".join(e.messages)
                
            await self.send(text_data=json.dumps({
                'type': 'bid_error',
                'error': error_msg
            }))

    async def bid_placed_event(self, event):
        # Rename event type for client consumption
        event['type'] = 'bid_update'
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_auction_state(self):
        auction = Auction.objects.get(id=self.room_name)
        return serialize_auction(auction)

    async def track_connection(self, connected):
        """Track active viewers for auction using Redis"""
        cache_key = f'auction_{self.room_name}_viewers'
        if connected:
            await database_sync_to_async(cache.get_or_set)(cache_key, 0)
            await database_sync_to_async(cache.incr)(cache_key)
        else:
            await database_sync_to_async(cache.decr)(cache_key)
        
        # Note: Ideally usage of Redis sets (sadd/srem) is better for accuracy
        # but requires raw redis client access. Using cache.incr for simplicity here.
        viewer_count = await database_sync_to_async(cache.get)(cache_key)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'viewer_count_update',
                'count': viewer_count
            }
        )

    async def viewer_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'viewers',
            'count': event['count']
        }))



