from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class AuctionItem(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    highest_bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='winning_auctions'
    )

    def __str__(self):
        return f"{self.title} - Rs.{self.current_price}"
    
    def check_expiration(self):
        if self.is_active and timezone.now() > self.end_time:
            self.is_active = False
            self.save()
            return True
        return False
    
class Bid(models.Model):
    item = models.ForeignKey(AuctionItem, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']

        
