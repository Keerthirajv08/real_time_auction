import logging
from django.utils import timezone

audit_logger = logging.getLogger('auctions.audit')

def log_bid_placed(user, auction, bid, ip_address):
    audit_logger.info('Bid placed', extra={
        'event': 'bid_placed',
        'bid_id': bid.id,
        'auction_id': auction.id,
        'user_id': user.id,
        'amount': bid.amount,
        'ip_address': ip_address,
        'timestamp': bid.timestamp.isoformat()
    })

    