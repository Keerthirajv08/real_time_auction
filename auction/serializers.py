#helper to format data for websockets since django rest framework doesn't support websockets
from rest_framework import serializers
from .models import Auction, Bid

def serialize_auction(auction):
    return {
        'id': auction.id,
        'title': auction.title,
        'current_price': str(auction.current_price),
        'end_time': auction.end_time.isoformat(),
        'status': auction.status,
        'version': auction.version,
    }

class BidSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Bid
        fields = ['id', 'user_name', 'amount', 'timestamp', 'status']


class AuctionSerializer(serializers.ModelSerializer):
    bids = BidSerializer(many=True, read_only=True)
    highest_bidder = serializers.CharField(source='get_highest_bidder', read_only=True)

    class Meta:
        model = Auction
        fields = ['id', 'title', 'description', 'current_price', 'end_time', 'status', 'version', 'bids', 'highest_bidder']


