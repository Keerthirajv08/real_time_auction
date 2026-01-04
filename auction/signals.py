from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings
import redis
from .models import Auction

r = redis.Redis.from_url(settings.CELERY_BROKER_URL)

EXPIRY_QUEUE_KEY = "auction:expiry_queue"

@receiver(post_save, sender=Auction)
def update_auction_heap(sender, instance, **kwargs):
    """ maintains the min-heap (Redis ZSET) in sync with the database.
        complexity: O(log N) - extremely fast.
    """
    if instance.status == 'active' and instance.end_time:
        #add to sorted set with score = Timestamp
        timestamp = instance.end_time.timestamp()

        #ZADD: key, mapping-{member: score}
        r.zadd(EXPIRY_QUEUE_KEY, {str(instance.id): timestamp})
    else:
        # if auction is paused, cancelled or closed, remove from queue
        r.zrem(EXPIRY_QUEUE_KEY, str(instance.id))

@receiver(post_delete, sender=Auction)
def remove_auction_from_heap(sender, instance, **kwargs):
    r.zrem(EXPIRY_QUEUE_KEY, str(instance.id))

