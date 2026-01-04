from django.db import models
#from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.
class Auction(models.Model):
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='auctions/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    min_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    end_time = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices = [('active', 'Active'), ('ended', 'Ended'), ('cancelled', 'Cancelled')],
        default='active'
    )

    version = models.IntegerField(default=0)

    highest_bidder = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winning_auctions'
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
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
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
     
class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('outbid', 'You were outbid'),
        ('winning', 'You are winning'),
        ('won', 'You won the auction'),
        ('ending_soon', 'Auction ending soon'),
        ('new_auction', 'New Auction in watched category'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='watched_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'auction')

    def __str__(self):
        return f"{self.user.username} watching {self.auction.title}"
    
    


