#helper to format data for websockets since django rest framework doesn't support websockets
#from rest_framework import serializers
#from .models import AuctionItem

def serialize_auction(auction):
    return {
        'id': auction.id,
        'title': auction.title,
        'current_price': str(auction.current_price),
        'end_time': auction.end_time.isoformat(),
        'status': auction.status,
        'version': auction.version,
    }

