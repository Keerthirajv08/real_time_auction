from django.contrib import admin

# Register your models here.
from auction.models import Auction, Bid

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'current_price', 'end_time', 'status', 'version')
    list_filter = ('status', 'created_at')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('auction', 'user', 'amount', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')


