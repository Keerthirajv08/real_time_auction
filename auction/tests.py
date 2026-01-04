import threading
from decimal import Decimal
from django.test import TransactionTestCase, TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from .models import Auction
from .services import BidService
from django.core.exceptions import ValidationError


# Create your tests here.
class ConcurrencyTests(TransactionTestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        
        self.auction = Auction.objects.create(
            title="Test Item",
            current_price=Decimal("100.00"),
            min_increment=Decimal("10.00"),
            end_time=timezone.now() + timezone.timedelta(hours=1),
            status='active'
        )
    
    def test_concurrent_bidding_same_price(self):
        bid_amount = Decimal("120.00")
        results = []

        def place_bid_wrapper(user):
            try:
                BidService.place_bid(self.auction.id, user, bid_amount)
                results.append(f"{user.username}: Success")
            except ValidationError as e:
                results.append(f"{user.username}: Failed - {e}")
            except Exception as e:
                results.append(f"{user.username}: Error - {e}")

        
        t1 = threading.Thread(target=place_bid_wrapper, args=(self.user1,))
        t2 = threading.Thread(target=place_bid_wrapper, args=(self.user2,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        print("\nTest Results:", results)

        success_count = sum(1 for r in results if "Success" in r)
        fail_count = sum(1 for r in results if "Failed" in r)

        self.assertEqual(success_count, 1, "Expected only one successful bid")
        self.assertEqual(fail_count, 1, "Expected only one failed bid")

        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price, bid_amount)
        self.assertEqual(self.auction.bids.count(), 1)

        

    
