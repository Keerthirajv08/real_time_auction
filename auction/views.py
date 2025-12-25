from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import AuctionItem, Bid


# Create your views here.
def index(request):
    active_auctions = AuctionItem.objects.filter(is_active=True).order_by('end_time')

    closed_auctions = AuctionItem.objects.filter(is_active=False).order_by('-end_time')[:5]

    return render(request, 'auction/index.html',{
        'active_auctions': active_auctions,
        'closed_auctions': closed_auctions
    })

def room(request, room_name):
    item = get_object_or_404(AuctionItem, id=room_name)

    item.check_expiration()

    previous_bids = item.bids.all().order_by('-timestamp')[:10]

    return render(request, 'auction/room.html',
                  {'room_name': room_name,
                   'item': item,
                   'previous_bids': previous_bids
                   })

@login_required
def place_bid(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed.'}, status=405)
    
    data = json.loads(request.body)
    new_amount = float(data.get('amount'))

    with transaction.atomic():
        item = AuctionItem.objects.select_for_update().get(id=item_id)

        if timezone.now() > item.end_time:
            return JsonResponse({'error': 'Auction is closed.'}, status=400)
        
        time_remaining = item.end_time - timezone.now()

        if time_remaining < timedelta(seconds=30):
            item.end_time = timezone.now() + timedelta(seconds=60)
            item.save()
            extension_triggered = True
        else:
            extension_triggered = False

        if not item.is_active:
            return JsonResponse({'error': 'Auction is closed.'}, status=400)
        
        if new_amount <= item.current_price:
            return JsonResponse({'error': 'Bid must be higher than current price'}, status=400)
        
        Bid.objects.create(item=item, user=request.user, amount=new_amount)
        item.current_price = new_amount
        item.highest_bidder = request.user
        item.save()

        channel_layer = get_channel_layer()
        group_name = f'auction_{item.id}'

        #print(f"DEBUG: User is in Group: {group_name}")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'auction_message',
                'message': f"{request.user.username} placed a bid of Rs.{new_amount}.",
                'message': f'New high bid: Rs.{new_amount}',
                'new_price': item.current_price,

                'new_end_time': item.end_time.isoformat()
            }
        )

    return JsonResponse({'status': 'success', 'new_price': new_amount})





