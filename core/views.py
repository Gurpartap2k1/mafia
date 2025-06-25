from django.shortcuts import redirect
from .forms import CreateGameForm


def landing(request):
    return render(request, 'core/landing.html')


from django.shortcuts import render, redirect, get_object_or_404

def join_room_landing(request, room_code):
    room_code = room_code.upper()  # Ensure uppercase consistency

    try:
        room = GameRoom.objects.get(code=room_code)
    except GameRoom.DoesNotExist:
        return render(request, 'core/game_already_started.html', {'error': 'Room not found.'})

    if room.started:
        return render(request, 'core/game_already_started.html', {'room': room})

    if request.session.get('player_id') and request.session.get('room_code') == room_code:
        return redirect('lobby', room_code=room.code)

    if request.method == 'POST':
        name = request.POST.get('name')

        if name:
            player = Player.objects.create(
                name=name,
                room=room,
                is_host=False
            )
            request.session['player_id'] = player.id
            request.session['room_code'] = room.code

            # Broadcast updated player list
            channel_layer = get_channel_layer()
            players = list(room.players.values_list('name', flat=True))
            async_to_sync(channel_layer.group_send)(
                f'lobby_{room.code}',
                {
                    'type': 'send_player_list',
                    'players': players
                }
            )

            return redirect('lobby', room_code=room.code)

        return render(request, 'core/join_room_landing.html', {
            'room': room,
            'error': 'Please enter your name.'
        })

    return render(request, 'core/join_room_landing.html', {'room': room})



def create_room(request):
    if request.method == 'POST':
        form = CreateGameForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            config = {
                'imposters': data['imposters'],
                'villagers': data['villagers'],
                'healers': data['healers'],
                'policemen': data['policemen'],
            }

            # Create room
            room = GameRoom.objects.create(
                host_name=data['host_name'],
                config=config,
            )

            # Add host as player
            player = Player.objects.create(
                name=data['host_name'],
                room=room,
                is_host=True
            )
            request.session['player_id'] = player.id

            return redirect('lobby', room_code=room.code)
    else:
        form = CreateGameForm()

    return render(request, 'core/create_room.html', {'form': form})



from django.shortcuts import render, get_object_or_404
from .models import GameRoom, Player

def lobby(request, room_code):
    room = get_object_or_404(GameRoom, code=room_code)
    all_players = room.players.all()
    non_host_players = all_players.filter(is_host=False)

    player_id = request.session.get('player_id')
    is_host = all_players.filter(id=player_id, is_host=True).exists()
    host_name = room.host_name
    config = room.config
    total_required = sum(config.values())

    context = {
        'room': room,
        'players': all_players,  # still list everyone
        'non_host_count': non_host_players.count(),
        'total_required': total_required,
        'join_link': request.build_absolute_uri(f'/join/{room.code}/'),
        'is_host': is_host,
        'host_name': host_name,
    }

    return render(request, 'core/lobby.html', context)


from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


from django.http import HttpResponseForbidden
import random

def start_game(request, room_code):
    room = get_object_or_404(GameRoom, code=room_code)

    host_player = Player.objects.filter(room=room, is_host=True).first()
    form_player_id = request.POST.get('player_id')
    session_player_id = request.session.get('player_id')

    print("== START GAME DEBUG ==")
    print("Host Player ID:", host_player.id if host_player else None)
    print("Session Player ID:", session_player_id)
    print("Form Player ID:", form_player_id)

    if not host_player:
        return HttpResponseForbidden("Host not found.")

    if str(host_player.id) != str(session_player_id) and str(host_player.id) != str(form_player_id):
        return HttpResponseForbidden("Only the host can start the game.")

    if room.started:
        return redirect('game', room_code=room.code)

    players = list(room.players.filter(is_host=False))
    random.shuffle(players)

    role_counts = room.config
    roles = (
        ['Imposter'] * role_counts['imposters'] +
        ['Villager'] * role_counts['villagers'] +
        ['Healer'] * role_counts['healers'] +
        ['Policeman'] * role_counts['policemen']
    )

    if len(roles) != len(players):
        return HttpResponseForbidden("Configured roles do not match number of players.")

    for player, role in zip(players, roles):
        player.role = role
        player.save()

    room.started = True
    room.save()

    channel_layer = get_channel_layer()
    for player in players:
        async_to_sync(channel_layer.group_send)(
            f"lobby_{room.code}",
            {
                'type': 'game_started',
                'player_id': player.id,
                'role': player.role,
            }
        )

    return redirect('game', room_code=room.code)

def game_view(request, room_code):
    room = get_object_or_404(GameRoom, code=room_code)
    player_id = request.session.get('player_id')
    player = get_object_or_404(Player, id=player_id, room=room)

    return render(request, 'core/game.html', {
        'room': room,
        'player': player,
    })


from django.views.decorators.http import require_POST

@require_POST
def kick_player(request, room_code, player_id):
    room = get_object_or_404(GameRoom, code=room_code)
    current_player_id = request.session.get('player_id')

    host = Player.objects.filter(room=room, is_host=True).first()
    if not host or host.id != current_player_id:
        return HttpResponseForbidden("Only the host can kick players.")

    player = get_object_or_404(Player, id=player_id, room=room)
    player.is_alive = False
    player.save()

    return redirect('game', room_code=room_code)


def end_game(request, room_code):
    room = get_object_or_404(GameRoom, code=room_code)

    # Get all players and their roles (no filtering on is_alive)
    players_data = list(room.players.values('name', 'role'))

    # Broadcast to game_<room_code>
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"game_{room.code}",
        {
            "type": "game_over",
            "players": players_data
        }
    )

    return redirect('game_over_page', room_code=room.code)


def game_over_page(request, room_code):
    room = get_object_or_404(GameRoom, code=room_code)
    players = room.players.all()
    return render(request, 'core/game_over.html', {
        'room': room,
        'players': players,
    })
