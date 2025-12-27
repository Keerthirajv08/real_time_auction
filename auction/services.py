from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Auction, Bid
from .audit import log_bid_placed 

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
    

