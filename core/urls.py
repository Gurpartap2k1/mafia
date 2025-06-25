from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('join/<str:room_code>/', views.join_room_landing, name='join_room_landing'),
    path('create/', views.create_room, name='create_room'),
    path('lobby/<str:room_code>/',views.lobby, name='lobby'),
    path('start/<str:room_code>/', views.start_game, name='start_game'),
    path('game/<str:room_code>/', views.game_view, name='game'),  # upcoming
    path('kick/<str:room_code>/<int:player_id>/', views.kick_player, name='kick_player'),
    path('room/<str:room_code>/end/', views.end_game, name='end_game'),
    path('game-over/<str:room_code>/', views.game_over_page, name='game_over_page'),

]