from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/auction/(?P<room_name>\w+)/$', consumers.AuctionConsumer.as_asgi()),

    re_path(r'ws/lobby/$', consumers.LobbyConsumer.as_asgi())
    
]

