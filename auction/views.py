from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import json
from django.db.models import F

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.core.exceptions import ValidationError

from .services import BidService

from .models import Auction, Bid, Watchlist



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

    is_watched = False
    if request.user.is_authenticated:
        is_watched = Watchlist.objects.filter(auction=auction, user=request.user).exists()

    if auction.status == 'active' and timezone.now() > auction.end_time:
        pass

    previous_bids = auction.bids.filter(status='accepted').order_by('-timestamp')[:10]

    return render(request, 'auction/room.html',
                  {'room_name': room_name,
                   'item': auction,
                   'auction': auction,
                   'previous_bids': previous_bids,
                   'is_watched': is_watched,
                   })

@login_required
def place_bid(request, item_id):
    """
    Place a bid on an auction item.

    Args:
        request (HttpRequest): The request sent by the client.
        item_id (int): The id of the auction item to bid on.

    Returns:
        JsonResponse: A JSON response containing the outcome of the bid.

    Raises:
        ValidationError: If the bid is invalid or the auction has already ended.
        Exception: If an internal error occurs.
    """
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


def signup_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}!")
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'auction/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                next_url = request.GET.get('next', 'index')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'auction/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

@login_required
def dashboard(request):
    user = request.user

    winning_auctions = Auction.objects.filter(
        status='active',
        highest_bidder=user,     
    ).order_by('-end_time')

    won_auctions = Auction.objects.filter(
        status='closed',
        highest_bidder=user,
    ).order_by('-end_time')

    watchlist = Watchlist.objects.filter(user=user).select_related('auction')

    return render(request, 'auction/dashboard.html', {
        'winning_auctions': winning_auctions,
        'won_auctions': won_auctions,
        'watchlist': watchlist
    })

@login_required
def toggle_watchlist(request, auction_id):
    auction = get_object_or_404(Auction, id=auction_id)

    existing = Watchlist.objects.filter(user=request.user, auction=auction).first()

    if existing:
        existing.delete()
        messages.info(request, f"Removed '{auction.title}' from watchlist.")
    else:
        Watchlist.objects.create(user=request.user, auction=auction)
        messages.info(request, f"Added '{auction.title}' to watchlist.")

    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))

def about(request):
    return render(request, 'auction/about.html')

