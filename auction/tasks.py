from celery import shared_task
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.conf import settings
import redis
from .models import Auction

r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
EXPIRY_QUEUE_KEY = "auction:expiry_queue"

@shared_task
def check_auction_expiry():
    """DSA Complexity: O(1) to check, O(K) to fetch K expired items."""
    now = timezone.now().timestamp()
    
    #expired_auctions = Auction.objects.filter(status='active', end_time__lte=now)
    expired_auctions = r.zrangebyscore(EXPIRY_QUEUE_KEY, '-inf', now)

    if not expired_auctions:
        return "No expired auctions found."
    
    ids_to_close = [int(aid) for aid in expired_auctions]
    auctions = Auction.objects.filter(id__in=ids_to_close, status='active')
    
    count = 0
    channel_layer = get_channel_layer()

    for auction in auctions:
        if auction.end_time.timestamp() > now:
            continue

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
    
    #remove expired auctions from queue in Redis to prevent infinite loop.
    if ids_to_close:
        r.zrem(EXPIRY_QUEUE_KEY, *ids_to_close)
        
    return f"{count} auctions closed."


