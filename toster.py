#!/usr/bin/env python3
import discord
import time
import os
import random
import re
import json

client = discord.Client()

DIRTY_THRESHOLD = 10 * 60
TOASTING_LOW_THRESHOLD = 60
TOASTING_HIGH_THRESHOLD = 120
SMOKING_GOOD_TOAST_CHANCES = 0.1


def wordsearch(word: str, msg: str, flags: int = re.I) -> bool:
    return re.search(r'\b' + word + r'\b', msg, flags) is not None


class TosterOopsie(RuntimeError):
    pass


class Toster:
    def __init__(self, backup_file):
        self.backup_file = backup_file
        self.guild = client.get_guild(297446629890457601)
        self.near_toster_channel = self.guild.get_channel(716707113401057430)
        try:
            with open(backup_file) as backup:
                j = json.load(backup)
                self.start_time = j["start_time"]
                self.toster_dirty = j["toster_dirty"]
        except FileNotFoundError as e:
            print(f"file {backup_file} doesn't exist: initializing new backup")
            self.start_time = None
            self.toster_dirty = 0
            self._save_state()
        except KeyError as e:
            print(f"file {backup_file} is corrupted: initializing new backup")
            self.start_time = None
            self.toster_dirty = 0
            self._save_state()
        # on other types of exceptions, application will just crash


    def _verify_user_near_toster(self, user):
        near_toster_users = self.near_toster_channel.members
        is_near_toster = user in near_toster_users
        if not is_near_toster:
            raise TosterOopsie('Musisz podejść do tostera!!')

    def _save_state(self):
        with open(self.backup_file, 'w') as f:
            state = {
                    "toster_dirty": self.toster_dirty,
                    "start_time": self.start_time
            }
            json.dump(state, f)

    def is_running(self):
        return self.start_time is not None

    def run(self, user):
        self._verify_user_near_toster(user)
        if self.is_running():
            raise TosterOopsie('Toster jest już włączony!!')
        self.start_time = time.time()
        self._save_state()

    def stop(self, user):
        self._verify_user_near_toster(user)
        if not self.is_running():
            raise TosterOopsie('Toster nie jest włączony!!')
        toasting_time = time.time() - self.start_time
        self.toster_dirty += toasting_time
        self.start_time = None
        self._save_state()
        return toasting_time

    def is_really_dirty(self):
        return self.toster_dirty >= DIRTY_THRESHOLD

    def is_dirty_at_all(self):
        return self.toster_dirty > 0

    def clean(self, user, *, amount=3*60):
        self._verify_user_near_toster(user)
        if self.is_running():
            raise TosterOopsie('Toster jest włączony')
        self.toster_dirty = max(self.toster_dirty - amount, 0)
        self._save_state()

toster = None

@client.event
async def on_ready():
    global toster
    print('We have logged in as {0.user}'.format(client))
    toster = Toster('/data/toster_state.json')

@client.event
async def on_message(message):
    global toster

    if message.author == client.user:
        return

    if client.user in message.mentions:
        try:
            if all(wordsearch(w, message.content) for w in ('czy', 'on')):
                if toster.is_running():
                    await message.channel.send('Toster jest włączony')
                else:
                    await message.channel.send('Toster nie jest włączony')
            elif all(wordsearch(w, message.content) for w in ('czy', 'brudny')):
                if toster.is_really_dirty():
                    await message.channel.send('Toster jest brudny!')
                elif toster.is_dirty_at_all():
                    await message.channel.send('Toster jest jeszcze względnie czysty?!')
                else:
                    await message.channel.send('Toster jest idealnie czysty?!?!')
            elif any(wordsearch(w, message.content) for w in ('umyj', 'wyczyść')):
                if toster.is_dirty_at_all():
                    toster.clean(message.author)
                    if toster.is_really_dirty():
                        await message.channel.send('Toster jest nadal brudny!')
                    elif toster.is_dirty_at_all():
                        await message.channel.send('Toster jest już względnie czysty')
                    else:
                        await message.channel.send('Toster jest teraz idealnie czysty?!?!', file=discord.File('toster_czyszczenie.gif'))
                else:
                    await message.channel.send('Toster już był idealnie czysty!')
            elif any(wordsearch(w, message.content) for w in ('włącz', 'on')):
                toster.run(message.author)
                await message.channel.send('Włączam toster')
            elif any(wordsearch(w, message.content) for w in ('wyłącz', 'off')):
                toasting_time = toster.stop(message.author)
                if toasting_time < TOASTING_LOW_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest niedopieczony!'.format(message.author), file=discord.File('tost_slaby.jpg'))
                elif toasting_time < TOASTING_HIGH_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest idealny!'.format(message.author), file=discord.File('tost_dobry.gif'))
                    if toster.is_really_dirty():
                        await message.channel.send('(tylko toster był tak trochę brudny...)')
                elif random.random() < SMOKING_GOOD_TOAST_CHANCES:
                    await message.channel.send('{0.mention} This toast is smoking good!'.format(message.author), file=discord.File('tost_smoking_good.jpg'))
                else:
                    await message.channel.send('{0.mention} Twój tost jest spalony!!'.format(message.author), file=discord.File('tost_spalony.jpg'))
            else:
                await message.channel.send('beep boop, jak będziesz źle obsługiwał toster to wywalisz korki')
        except TosterOopsie as e:
            await message.channel.send(e.args[0])

    if all(wordsearch(w, message.content) for w in ('czy', 'ser')):
        await message.channel.send('{0.mention} Oczywiście że jest! Sera dla uczestników nigdy nie braknie'.format(message.author))

client.run(os.environ['DISCORD_TOKEN'])
