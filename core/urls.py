from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_room, name='create_room'),
    path('lobby/<str:room_code>/',views.lobby, name='lobby'),
    path('join/<str:room_code>/', views.join_room, name='join_room'),
    path('start/<str:room_code>/', views.start_game, name='start_game'),
    path('game/<str:room_code>/', views.game_view, name='game'),  # upcoming
    path('kick/<str:room_code>/<int:player_id>/', views.kick_player, name='kick_player'),
    path('end/<str:room_code>/', views.end_game, name='end_game'),

]