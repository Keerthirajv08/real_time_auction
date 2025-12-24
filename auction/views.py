from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
from .models import AuctionItem, Bid


# Create your views here.
def index(request):
    return render(request, 'auction/index.html')

def room(request, room_name):
    return render(request, 'auction/room.html',
                  {'room_name': room_name
                   })

@login_required
def place_bid(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed.'}, status=405)
    
    data = json.loads(request.body)
    new_amount = float(data.get('amount'))

    with transaction.atomic():
        item = AuctionItem.objects.select_for_update().get(id=item_id)

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

        print(f"DEBUG: User is in Group: {group_name}")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'auction_message',
                'message': f"{request.user.username} placed a bid of Rs.{new_amount}.",
                'message': f'New high bid: Rs.{new_amount}',
                'new_price': item.current_price
            }
        )


    return JsonResponse({'status': 'success', 'new_price': new_amount})



