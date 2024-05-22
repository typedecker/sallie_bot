# -*- coding: utf-8 -*-
"""
Created on Tue May 21 20:02:05 2024

@author: ketch
"""

import nest_asyncio
nest_asyncio.apply()

import discord, pyrebase, os, asyncio, flask
from discord.ext import tasks
from gtts import gTTS
from flask import Flask
from datetime import datetime
from threading import Thread

import datetime as dt

os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.abspath('assets')
import ffmpeg

datetime_date_format = '%a %d %b %Y, %I:%M:%S %p UTC time'
CONFESSION_CHANNEL_ID = 1239309061585899572

# -------------------------------
app = Flask('')

@app.route('/')
def main():
    return "Status: Online(Deployed at {utc_time})".format(utc_time = datetime.utcnow().strftime(datetime_date_format))

def run() :
    PORT = 49152
    port_found = False
    while not port_found :
        try :
            app.run(host="0.0.0.0", port = PORT)
            port_found = True
            print('Bot is now running on port: {port}'.format(port = PORT))
        except :
            print('Port({port}) is already in use, checking a new port...'.format(port = PORT))
            port_found = False
            PORT += 1
        continue
    return

def keep_alive():
    server = Thread(target=run)
    server.start()
    return

# -------------------------------

#---------DATABASE SETUP----------
# Initializes the configurations for the firebase realtime database.
database_config = {          
                    "apiKey" : os.environ['FIREBASE_API_KEY'],
                    "authDomain" : "sallie-b93a6.firebaseapp.com",
                    "databaseURL" : "https://sallie-b93a6-default-rtdb.firebaseio.com",
                    "projectId" : "sallie-b93a6",
                    "storageBucket" : "sallie-b93a6.appspot.com",
                  }

firebase_client = pyrebase.initialize_app(database_config) # Intializes the firebase client object.
firebase_db_obj = firebase_client.database() # Initializes the firebase database object.
#---------------------------------

intents = discord.Intents.all()
bot = discord.Client(intents = intents)

voice_client = None

@bot.event
async def on_ready() :
    bot_activity = discord.Game(name = 'Getting Slapped by the slappers!', start = bot.user.created_at)
    await bot.change_presence(activity = bot_activity)
    
    print('[LOG] Beam me up scotty ;)')
    return

@bot.event
async def on_message(message) :
    global voice_client
    
    print(f'[MESSAGE LOG]: {message.author} | {message.content}')
    if message.interaction != None :
        print(f'INTERACTION DETECTED SEXY BOI {message.interaction.user.name} | {message.interaction.name}')
        
        if message.interaction.name == 'bump' :
            await message.channel.send(f'HEY THANKS {message.interaction.user.mention} FOR BUMPING MAN, I DETECTED IT CUZ YOU ARE SO SEXY!!!')
        return
        
    if message.content.lower() == '$$ping' :
        await message.channel.send('Bot has been successfully pinged({} ms)! tyy <33~'.format(round((bot.latency * 1000), 2)))
    if message.content.lower() == '$$slap' :
        await message.channel.send(':lizard: :wave::skin-tone-1: *You slapped sallie gently and gained some slapping experience!!* Keep slapping dem cheeks you slappy boi!')
        poo = firebase_db_obj.child('slap').child('count').get().val()
        firebase_db_obj.child('slap').child('count').child(message.author.name).set(poo + 1)
        print(type(poo))
        return
    if message.content.startswith('$$confess ') :
        confession = message.content[len('$$confess') : ]
        embed = discord.Embed(color = discord.Colour.dark_green(), title = 'Anonymous Confession', description = confession)
        confession_channel = await bot.fetch_channel(CONFESSION_CHANNEL_ID)
        confession_msg = await confession_channel.send(embed = embed)
        if not isinstance(message.channel, discord.DMChannel) :
            await message.delete()
            if not message.author.dm_channel :
                await message.author.create_dm()
            await message.author.dm_channel.send(f'Confession sent!! {confession_msg.jump_url}')
        else :
            await message.reply(f'Confession sent!! {confession_msg.jump_url}')
    if message.content.lower() == '$$vc_connect' :
        try :
            voice_client = await message.author.voice.channel.connect()
            await message.channel.send('Connected to {vc_name}!'.format(vc_name = message.author.voice.channel.name))
            # music_cmd_channel_id = message.channel.id
        except :
            if message.author.voice.channel == None :
                await message.channel.send('You are not in a VC rn! Join a VC first!!')
            else :
                await message.channel.send('Could not connect to VC due to some issue.')
    if message.content.lower() == '$$vc_disconnect' :
        if voice_client == None :
            await message.channel.send('The bot is not in a VC rn.')
        else :
            if voice_client.is_playing() :
                voice_client.stop()
            await voice_client.disconnect()
            voice_client = None
            await message.channel.send('Disconnected!')
            # music_queue.clear()
            # music_cmd_channel_id, currently_playing = None, None
    if message.content.lower().startswith('$$tts ') :
        await message.add_reaction('🔊')
        tts_obj = gTTS(text = message.content.lower()[len('$$tts ') : ], tld = 'us', slow = False)
        tts_obj.save('temp_tts.mp3')
        if voice_client == None :
            try :
                voice_client = await message.author.voice.channel.connect()
                audio_source = discord.FFmpegPCMAudio('temp_tts.mp3')
                if not voice_client.is_playing():
                    voice_client.play(audio_source, after = None)
                while voice_client.is_playing() :
                    await asyncio.sleep(1)
                await voice_client.disconnect()
            except :
                if message.author.voice.channel == None :
                    await message.channel.send('You are not in a VC rn! Join a VC first!!')
                else :
                    await message.channel.send('Could not connect to VC due to some issue.')
        else :
            audio_source = discord.FFmpegPCMAudio('temp_tts.mp3')
            if not voice_client.is_playing():
                voice_client.play(audio_source, after = None)

    return

if __name__ == '__main__' :
    BOT_TOKEN = os.environ['BOT_TOKEN']
    bot.run(BOT_TOKEN)