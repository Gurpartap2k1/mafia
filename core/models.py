import string

from django.db import models
import random

roles = [
    ('Imposter', 'Imposter'),
    ('Villager', 'Villager'),
    ('Doctor', 'Doctor'),
    ('Policeman', 'Policeman'),
]

def generate_room_code(length = 6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


class GameRoom(models.Model):
    code = models.CharField(max_length=8, unique=True, default=generate_room_code)
    host_name = models.CharField(max_length=200)
    config = models.JSONField(default=dict)
    started = models.BooleanField(default=False)
    ended = models.BooleanField(default=False)

    def __str__(self):
        return f"Room {self.code}"


class Player(models.Model):
    name = models.CharField(max_length=200)
    room = models.ForeignKey(GameRoom, related_name='players', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices= roles, blank=True, null=True)
    is_alive = models.BooleanField(default=True)
    is_host = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({'Host' if self.is_host else 'Player'})"

