from decimal import Decimal
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
        
        last_bid = auction.bids.filter(status='accepted').order_by('-timestamp').first()

        if last_bid and last_bid.user == user:
            raise ValidationError("You are already the highest bidder")
        
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

        log_bid_placed(bid, auction, user, ip_address)

        return bid, auction
    

class NotificationService:
    @staticmethod
    def notify_outbid(previous_bidder, auction, new_amount):
        notification = Notification.objects.create(
            user=previous_bidder,
            notification_type='outbid',
            auction=auction,
            message=f"you were outbid on '{auction.title}'. New bid: Rs.{new_amount}"
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{previous_bidder.id}',
            {
                'type': 'notification',
                'notification': 
                    {
                        'id': notification.id,
                        'type': notification.notification_type,
                        'message': notification.message,
                        'auction_id': notification.auction.id,
                        'timestamp': notification.created_at.isoformat()
                    }   
            }
        )

        if previous_bidder.profile.email_notifications:
            send_email_notification.delay(previous_bidder, notification.id)

        
    @staticmethod
    def notify_auction_ending_soon(auction):
        bidders = User.objects.filter(
            bids__auction=auction
        ).distinct()

        for bidder in bidders:
            notification = Notification.objects.create(
                user=bidder,
                notification_type='ending_soon',
                auction=auction,
                message=f"Auction '{auction.title}' is ending soon."                
            )

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{bidder.id}',
                {
                    'type': 'notification',
                    'notification': 
                        {
                            'id': notification.id,
                            'type': notification.notification_type,
                            'message': notification.message,
                            'auction_id': notification.auction.id,
                            'timestamp': notification.created_at.isoformat()
                        }   
                }
            )

