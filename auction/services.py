from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Auction, Bid, Notification
from .audit import log_bid_placed 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User 

class BidService:
    @staticmethod
    @transaction.atomic
    def place_bid(auction_id, user, amount, ip_address=None):
        """ atomically place a bid with optimistic locking"""
        try:
            auction = Auction.objects.select_for_update().get(id=auction_id)
        except Auction.DoesNotExist:
            raise ValidationError("Auction not found")
        
        if auction.status != 'active':
            raise ValidationError("Auction is not active")
        
        if timezone.now() > auction.end_time:
            raise ValidationError("Auction has ended")
        
        if amount <= auction.current_price:
            raise ValidationError(
                f"Bid must be higher than current price: {auction.current_price}")
        
        if amount < auction.current_price + auction.min_increment:
            raise ValidationError(
                f"Bid must be at least {auction.min_increment} higher"
            )
        
        #last_bid = auction.bids.filter(status='accepted').order_by('-timestamp').first()
        #if last_bid and last_bid.user == user:
           # raise ValidationError("You are already the highest bidder")

        #remember the previous highest bidder BEFORE creating the new bid
        previous_bid = auction.bids.filter(status='accepted').order_by('-timestamp').first()
        previous_bidder = previous_bid.user if previous_bid else None
        
        #create the new bid and update the auction logic ...
        bid = Bid.objects.create(
            auction=auction, 
            user=user,
            amount=amount,
            status='accepted',
            ip_address=ip_address
        )

        auction.current_price = amount
        auction.version += 1
        auction.save()
       
        log_bid_placed(user, auction, bid, ip_address)

        #......[Broadcast to Room].....
        channel_layer  = get_channel_layer()
        '''async_to_sync(channel_layer.group_send)(
            f'auction_{auction.id}',
            {
                'type': 'auction_message',
                'message': f'New high bid: Rs.{amount} by {user.username}',
                'new_price': str(amount),
                'bidder_name': user.username,
                'new_end_time': auction.end_time.isoformat() if auction.end_time else None
            }
        )'''

        #2. Notify the OUTBID user (if they are different from current bidder)
        if previous_bidder and previous_bidder != user:
            Notification.objects.create(
                user=previous_bidder,
                auction=auction,
                notification_type='outbid',
                message=f"You have been outbid on {auction.title}!"
            )

            async_to_sync(channel_layer.group_send)(
                f"user_{previous_bidder.id}",
                {
                    'type': 'notification',
                    'notification_type': 'outbid',
                    'message': f"⚠️ You have been outbid on {auction.title}! New bid: Rs.{amount}"
                }
            )
        
        def send_websocket_update():
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'auction_{auction.id}',
                {
                    'type': 'auction_message',
                    'message': f'New high bid: Rs. {amount} by {user.username}',
                    'new_price': str(amount),
                    'new_end_time': auction.end_time.isoformat() if auction.end_time else None
                }
            )

        transaction.on_commit(send_websocket_update)

        return bid, auction
    
