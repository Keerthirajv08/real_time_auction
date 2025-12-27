from django.db import models
from django.conf import settings
from django.contrib.auth.models import User 
from django.utils import timezone


# Create your models here.
class Auction(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    version = models.IntegerField(default=0)
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices = [('active', 'Active'), ('ended', 'Ended'), ('cancelled', 'Cancelled')],
        default='active'
    )

    version = models.IntegerField(default=0)

    highest_bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='Winning_auctions'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'end_time']),
            models.Index(fields=['created_at']),
        ]
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
   
class Bid(models.Model):
    #item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='bids')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    #user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')],
        default='pending'
    )
    ip_address = models.GenericIPAddressField(null=True)

    class Meta:
        indexes = [
            models.Index(fields=['auction', 'timestamp']),
            models.Index(fields=['user', '-timestamp']),
        ]
        
        ordering = ['-timestamp']

        

