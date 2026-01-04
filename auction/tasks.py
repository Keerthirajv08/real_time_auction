from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Auction

@shared_task
def check_auction_expiry():
    now = timezone.now()
    
    expired_auctions = Auction.objects.filter(status='active', end_time__lte=now)

    if not expired_auctions.exists():
        return "No expired auctions found."
    
    count = 0
    channel_layer = get_channel_layer()

    for auction in expired_auctions:
        auction.status = 'closed'
        auction.save()
        count += 1

        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'auction_{auction.id}',
                {
                    'type': 'auction_message',
                    'message': 'Auction closed.',
                    'new_price': str(auction.current_price),
                    'status': 'closed'
                }
            )
        
    return f"{count} auctions closed."


