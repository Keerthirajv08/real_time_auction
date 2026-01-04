from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from decimal import Decimal, InvalidOperation

from .models import Auction, Bid
from .serializers import AuctionSerializer, BidSerializer
from .services import BidService

from rest_framework.throttling import UserRateThrottle, ScopedRateThrottle

class AuctionViewSet(viewsets.ModelViewSet):
    queryset = Auction.objects.all().order_by('-created_at')
    serializer_class = AuctionSerializer

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=['POST'], permission_classes=[permissions.IsAuthenticated], throttle_classes=[ScopedRateThrottle])
    def bid(self, request, pk=None):
        #print(f"DEBUG: Received data:{request.data}")
        #print(f"DEBUG: Content Type: {request.content_type}")
        auction = self.get_object()
        self.throttle_scope = 'bidding'

        amount_str = request.data.get('amount')
        if amount_str is None:
            return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            amount_str = str(amount_str).strip()
            amount = Decimal(amount_str)

            bid, auction = BidService.place_bid(
                auction_id=auction.id,
                user=request.user,
                amount=amount,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            return Response(BidSerializer(bid).data, status=201)
        except InvalidOperation:
            return Response({'error': f'Invalid amount: "{amount_str}". Please send a valid number like "150.00".'},
                            status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
class BidViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bid.objects.all().order_by('-timestamp')
    serializer_class = BidSerializer
    
   
           
        

