from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    #path('room/<str:room_name>/', views.room, name='room'),
    path('<str:room_name>/', views.room, name='room'),
    path('api/bid/<int:item_id>/', views.place_bid, name='place_bid'),
]



