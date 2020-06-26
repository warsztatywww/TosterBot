#!/usr/bin/env python3
import discord
import time
import os
import random

client = discord.Client()

toster_start_time = None
toster_dirty = 0

DIRTY_THRESHOLD = 10 * 60
TOASTING_LOW_THRESHOLD = 60
TOASTING_HIGH_THRESHOLD = 120
SMOKING_GOOD_TOAST_CHANCES = 0.1

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    global toster_start_time, toster_dirty

    if message.author == client.user:
        return

    if client.user in message.mentions:
        if 'czy' in message.content.lower() and 'włączony' in message.content.lower():
            if toster_start_time:
                await message.channel.send('Toster jest włączony')
            else:
                await message.channel.send('Toster nie jest włączony')
        elif 'czy' in message.content.lower() and 'brudny' in message.content.lower():
            if toster_dirty >= DIRTY_THRESHOLD:
                await message.channel.send('Toster jest brudny!')
            elif toster_dirty > 0:
                await message.channel.send('Toster jest jeszcze względnie czysty?!')
            else:
                await message.channel.send('Toster jest idealnie czysty?!?!')
        elif 'umyj' in message.content.lower() or 'wyczyść' in message.content.lower():
            if toster_dirty > 0:
                toster_dirty = max(toster_dirty - 3 * 60, 0)
                if toster_dirty >= DIRTY_THRESHOLD:
                    await message.channel.send('Toster jest nadal brudny!')
                elif toster_dirty > 0:
                    await message.channel.send('Toster jest już względnie czysty')
                else:
                    await message.channel.send('Toster jest teraz idealnie czysty?!?!', file=discord.File('toster_czyszczenie.gif'))
            else:
                await message.channel.send('Toster już był idealnie czysty!')
        elif 'włącz' in message.content.lower() or 'on' in message.content.lower():
            if not toster_start_time:
                toster_start_time = time.time()
                await message.channel.send('Włączam toster')
            else:
                await message.channel.send('Toster jest już włączony!!')
        elif 'wyłącz' in message.content.lower() or 'off' in message.content.lower():
            if toster_start_time:
                toasting_time = time.time() - toster_start_time
                toster_dirty += toasting_time
                toster_start_time = None
                if toasting_time < TOASTING_LOW_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest niedopieczony!'.format(message.author), file=discord.File('tost_slaby.jpg'))
                elif toasting_time < TOASTING_HIGH_THRESHOLD:
                    await message.channel.send('{0.mention} Twój tost jest idealny!'.format(message.author), file=discord.File('tost_dobry.gif'))
                    if toster_dirty >= DIRTY_THRESHOLD:
                        await message.channel.send('(tylko toster był tak trochę brudny...)')
                elif random.random() < SMOKING_GOOD_TOAST_CHANCES:
                    await message.channel.send('{0.mention} This toast is smoking good!'.format(message.author), file=discord.file('tost_smoking_good.jpg'))
                else:
                    await message.channel.send('{0.mention} Twój tost jest spalony!!'.format(message.author), file=discord.File('tost_spalony.jpg'))
            else:
                await message.channel.send('Toster nie jest włączony!')
        else:
            await message.channel.send('beep boop, jak będziesz źle obsługiwał toster to wywalisz korki')

    if 'czy' in message.content.lower() and 'ser' in message.content.lower() and '?' in message.content.lower():
        await message.channel.send('{0.mention} Oczywiście że jest! Sera dla uczestników nigdy nie braknie'.format(message.author))

client.run(os.environ['DISCORD_TOKEN'])
