import time
from django.conf import settings
from django_redis import get_redis_connection
from .models import Auction

class TrendingAuctionCache:
    KEY = "trending_auctions_lru"
    CAPACITY = 10 

    @staticmethod
    def record_view(auction_id):
        """ DSA: LRU 'Put' Operation
        Moves item to 'Front' based on highest score by updating its timestamp.
        Complexity: O(log N) in Redis """
        connection = get_redis_connection("default")
        now = time.time()

        connection.zadd(TrendingAuctionCache.KEY, {str(auction_id): now})

        if connection.zcard(TrendingAuctionCache.KEY) > TrendingAuctionCache.CAPACITY:
            connection.zremrangebyrank(TrendingAuctionCache.KEY, 0, -(TrendingAuctionCache.CAPACITY + 1))

    
    @staticmethod
    def get_top_items():
        connection = get_redis_connection("default")

        auction_ids = connection.zrevrange(TrendingAuctionCache.KEY, 0, TrendingAuctionCache.CAPACITY - 1)

        if not auction_ids:
            return []
        
        #convert bytes to int
        ids = [int(aid) for aid in auction_ids]

        #fetch actual objects from DB (optimized: 1 Query)
        auctions = list(Auction.objects.filter(id__in=ids))

        #Sort the DB results to match the Redis order (LRU order)
        auctions.sort(key=lambda t: ids.index(t.id))

        return auctions

