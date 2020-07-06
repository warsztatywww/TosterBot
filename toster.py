#!/usr/bin/env python3
import discord
import time
import os
import random
import re
import json
import asyncio

client = discord.Client()

DIRTY_THRESHOLD = 10 * 60
TOASTING_LOW_THRESHOLD = 60
TOASTING_HIGH_THRESHOLD = 120
SMOKING_GOOD_TOAST_CHANCES = 0.1
TOAST_STORAGE_TIMEOUT = 10 * 60


def wordsearch(word: str, msg: str, flags: int = re.I) -> bool:
    return re.search(r'\b' + word + r'\b', msg, flags) is not None


class TosterOopsie(RuntimeError):
    pass


class Toster:
    def __init__(self, backup_file):
        self.backup_file = backup_file
        self.guild = client.get_guild(729268066306883594)
        self.near_toster_channel = self.guild.get_channel(729268066306883598)
        try:
            with open(backup_file) as backup:
                j = json.load(backup)
                self.start_time = j["start_time"]
                self.toster_dirty = j["toster_dirty"]
                self.users_with_toasts = j["users_with_toasts"]
        except FileNotFoundError as e:
            print(f"file {backup_file} doesn't exist: initializing new backup")
            self.start_time = None
            self.toster_dirty = 0
            self.users_with_toasts = {}
            self._save_state()
        except KeyError as e:
            print(f"file {backup_file} is corrupted: initializing new backup")
            self.start_time = None
            self.toster_dirty = 0
            self.users_with_toasts = {}
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
                    "start_time": self.start_time,
                    "users_with_toasts": self.users_with_toasts
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

    def update_users_data(self):
        for user in self.users_with_toasts.keys():
            for toast in self.users_with_toasts[user]:
                if time.time() - toast[1] > TOAST_STORAGE_TIMEOUT:
                    self.users_with_toasts[user].remove(toast)
        self._save_state()

toster = None

@client.event
async def on_ready():
    global toster
    print('We have logged in as {0.user}'.format(client))
    toster = Toster('/data/toster_state.json')
    asyncio.create_task(update_presence())

last_msg = None
async def update_presence():
    global toster, client, last_msg
    while True:
        msg = None
        if toster.is_running():
            msg = "Tost się tostuje od " + str(int((time.time() - toster.start_time)/5)*5) + " s 🍞"
        else:
            if toster.is_really_dirty():
                msg = 'Toster jest brudny! :('
            elif toster.is_dirty_at_all():
                msg = 'Toster jest jeszcze względnie czysty'
            else:
                msg = 'Toster jest idealnie czysty?!?!'
        if msg != last_msg:
            await client.change_presence(status=discord.Status.online if toster.is_running() else discord.Status.idle, activity=discord.Game(name=msg))
            last_msg = msg
        await asyncio.sleep(1)

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
                if str(message.author) not in toster.users_with_toasts.keys():
                    toster.users_with_toasts[str(message.author)] = []
                if toasting_time < TOASTING_LOW_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest niedopieczony!'.format(message.author), file=discord.File('tost_slaby.jpg'))
                    toster.users_with_toasts[str(message.author)].append(['niedopieczony',time.time()])
                elif toasting_time < TOASTING_HIGH_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest idealny!'.format(message.author), file=discord.File('tost_dobry.gif'))
                    toster.users_with_toasts[str(message.author)].append(['idealny', time.time()])
                    if toster.is_really_dirty():
                        await message.channel.send('(tylko toster był tak trochę brudny...)')
                elif random.random() < SMOKING_GOOD_TOAST_CHANCES:
                    await message.channel.send('{0.mention} This toast is smoking good!'.format(message.author), file=discord.File('tost_smoking_good.jpg'))
                    toster.users_with_toasts[str(message.author)].append(['smoking good', time.time()])
                else:
                    await message.channel.send('{0.mention} Twój tost jest spalony!!'.format(message.author), file=discord.File('tost_spalony.jpg'))
                    toster.users_with_toasts[str(message.author)].append(['spalony', time.time()])
                toster.update_users_data()
            elif any(wordsearch(w,message.content) for w in ("oddaj","give", "daj", "przekaż")): 
                toster.update_users_data()
                if str(message.author) in toster.users_with_toasts.keys() and len(toster.users_with_toasts[str(message.author)]) >= len(message.mentions) - 1: 
                    print(message.mentions)
                    if len(message.mentions) > 1:
                        gifted_users = message.mentions
                        gifted_users.remove(client.user)
                        if len(gifted_users) == 1:
                            mess = '{0.mention} oddałeś swojego tosta {0.mention}'
                        else:
                            mess = '{0.mention} oddałeś swojego tosta ' + "{0.mention}, " * max((len(gifted_users) - 2),0) + "{0.mention} i {0.mention}"
                        mess = mess.format(message.author)
                        for gifted_user in gifted_users:
                            mess = mess.format(gifted_user)
                        await message.channel.send(mess) 
                        for gifted_user in gifted_users:
                            tost = toster.users_with_toasts[str(message.author)].pop(0)
                            await gifted_user.send('{0.mention} upiekł dla ciebie tosta!!!'.format(message.author))
                            if tost[0] == 'niedopieczony':
                                await gifted_user.send("Tost jest niedopieczony!", file=discord.File('tost_slaby.jpg'))
                            elif tost[0] == 'idealny':
                                await gifted_user.send("Tost jest idealny!", file=discord.File('tost_dobry.gif'))
                            elif tost[0] == 'smoking good':
                                await gifted_user.send("This toast is smoking good!", file=discord.File('tost_smoking_good.jpg'))
                            else:
                                await gifted_user.send("Tost jest spalony!!", file=discord.File('tost_spalony.jpg'))
                            if not str(gifted_user) in toster.users_with_toasts.keys():
                                toster.users_with_toasts[str(gifted_user)] = []
                            toster.users_with_toasts[str(gifted_user)].append(tost)
                        toster.update_users_data()
                    else:
                        await message.channel.send("{0.mention} nie podałeś komu chcesz oddać tosta".format(message.author)) 

                
                else: 
                    await message.channel.send('{0.mention} nie masz wystarczającej ilości tostów'.format(message.author)) 



            elif all(wordsearch(w, message.content) for w in ('how','many')) or all(wordsearch(w, message.content) for w in ('ile','tostów')) or all(wordsearch(w, message.content) for w in ('czy','tosty')) :
                toster.update_users_data()

                if str(message.author) not in toster.users_with_toasts:
                    await message.channel.send("{0.mention} Nie masz żadnych tostów".format(message.author))
                else:
                    tosty = len(toster.users_with_toasts[str(message.author)])
                    mess = '{0.mention} masz '.format(message.author)
                    if tosty == 1:
                        mess += '1 tosta'
                        
                    elif tosty > 1 and tosty < 5:
                        mess += "{} tosty".format(tosty)
                    else:
                        mess += "{} tostów".format(tosty)
                    await message.channel.send(mess)
        

            else:
                await message.channel.send('beep boop, jak będziesz źle obsługiwał toster to wywalisz korki')
        except TosterOopsie as e:
            await message.channel.send(e.args[0])

    if all(wordsearch(w, message.content) for w in ('czy', 'ser')):
        await message.channel.send('{0.mention} Oczywiście że jest! Sera dla uczestników nigdy nie braknie'.format(message.author))

client.run(os.environ['DISCORD_TOKEN'])

#TODO: sprawdzić czy można wywalić zapisywanie w którychś miejscach
