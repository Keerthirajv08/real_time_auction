from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json
from django.db.models import F

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError

from .services import BidService

from .models import Auction, Bid



def index(request):
    #active_auctions = AuctionItem.objects.filter(is_active=True).order_by('end_time')
    
    active_auctions = Auction.objects.filter(status='active').order_by('end_time')

    #closed_auctions = AuctionItem.objects.filter(is_active=False).order_by('-end_time')[:5]
    closed_auctions = Auction.objects.filter(status='closed').order_by('-end_time')[:5]

    return render(request, 'auction/index.html',{
        'active_auctions': active_auctions,
        'closed_auctions': closed_auctions
    })


def room(request, room_name):
    auction = get_object_or_404(Auction, id=room_name)

    if auction.status == 'active' and timezone.now() > auction.end_time:
        pass

    previous_bids = auction.bids.filter(status='accepted').order_by('-timestamp')[:10]

    return render(request, 'auction/room.html',
                  {'room_name': room_name,
                   'item': auction,
                   'previous_bids': previous_bids
                   })

@login_required
def place_bid(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed.'}, status=405)
    
    try:
        data = json.loads(request.body)
        new_amount = float(data.get('amount'))
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid bid amount.'}, status=400)
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    try:
        bid, auction = BidService.place_bid(
            auction_id=item_id,
            user=request.user,
            amount=new_amount,
            ip_address=ip
        )
        
        return JsonResponse({
            'status': 'success',
            'new_price': bid.amount,
            'new_end_time': auction.end_time.isoformat()
        })

    except ValidationError as e:
        return JsonResponse({'error': str(e.message)}, status=400)
    
    except Exception as e:
        return JsonResponse({'error': 'An internal error occured.'}, status=500)


    '''auction = get_object_or_404(Auction, id=item_id)

    if auction.status != 'active' or timezone.now() > auction.end_time:
        return JsonResponse({'error': 'Auction is closed.'}, status=400)
    
    if new_amount <= auction.current_price:
        return JsonResponse({'error': 'Bid must be higher than current price.'}, status=400)
    
    time_remaining = auction.end_time - timezone.now()
    new_end_time = auction.end_time
    if time_remaining < timedelta(seconds=30):
        new_end_time = timezone.now() + timedelta(seconds=60)

    rows_updated = Auction.objects.filter(
        id=auction.id,
        version=auction.version
    ).update(
        current_price=new_amount,
        end_time=new_end_time,
        version=F('version') + 1,
        updated_at=timezone.now()
    )

    if rows_updated == 0:
        return JsonResponse({'error': 'Bid conflict: Someone bid before you. Please retry.'}, status=400)
    
    Bid.objects.create(
        auction=auction,
        user=request.user,
        amount=new_amount,
        status='accepted'
    )

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'auction_{item_id}',
        {
            'type': 'auction_message',
            'message': f'New high bid: Rs.{new_amount}',
            'new_price': new_amount,
            'new_end_time': new_end_time.isoformat()
        }
    )

    return JsonResponse({'status': 'success', 'new_price': new_amount})'''


'''class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all()
    serializer_class = AuctionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def bid(self, request, pk=None):
        auction = self.get_object()
        amount = request.data.get('amount')

        try:
            bid, updated_auction = BidService.place_bid(
                auction_id=auction.id,
                user=request.user,
                amount=amount,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except ValidationError as e:
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'auction_{auction.id}',
            {
                'type': 'auction_message',
                'message': f'New high bid: Rs.{bid.amount}',
                'new_price': str(bid.amount),
                'new_end_time': updated_auction.end_time.isoformat()
            }
        )

        return Response({
            'status': 'success',
            'new_price': bid.amount,
            'bid_id': bid.id,   
        }, status=status.HTTP_200_OK)

'''


