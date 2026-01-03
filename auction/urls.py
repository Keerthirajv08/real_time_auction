from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import api_views

router = DefaultRouter()
router.register(r'auctions', api_views.AuctionViewSet)
router.register(r'bids', api_views.BidViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('room/<str:room_name>/', views.room, name='room'),
    path('api/bid/<int:item_id>/', views.place_bid, name='place_bid'),
    path('api/v1/', include(router.urls)),

    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]




