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
SLAPPING_SALAMANDER_SERVER_ACCENT = '#F05E22'
CONFESSION_CHANNEL_ID = 1239309061585899572
BOT_OWNER_ID = 568446269610000385
PET_OWNER_GUILD = 1230967641200394302

HELP_DICT = {
            'ping': ['$$ping', 'Pong! Returns the ping in milliseconds for the bot.'],
            'help': ['$$help <optional:query>', 'Provided with a list of all commands available, if the optionary query is provided then it describes the command being queried.'],
            'slap': ['$$slap', 'Slaps sallie and rewards you with exp points(W.I.P.)'],
            'confess': ['$$confess <confession>', 'Posts an anonymous confession message in the confessions channel of the server with the content provided, can be used via DMs as well.'],
            'vc_connect': ['$$vc_connect', 'Connects to the same VC as the user who executed the command.'],
            'vc_disconnect': ['$$vc_disconnect', 'Disconnects from any VC that she might be in.'],
            'tts' : ['$$tts <message>', 'Converts the message from text to speech and plays it in VC.']
            }

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

async def review_ping_check(members) :
    print('[LOG] Review ping check is under way.')
    REVIEW_PING_ROLE_ID = 1242796399754743808
    REVIEW_PING_CHANNEL_ID = 1242796180359086130
    
    review_ping_channel = bot.fetch_channel(REVIEW_PING_CHANNEL_ID)
    for member in members :
        found_role_list = [role for role in member.roles if role.id == REVIEW_PING_ROLE_ID]
        print(f'[LOG] Review availability is being examined for {member.name} right now... {(datetime.utcnow() - member.joined_at)}')
        if any(found_role_list) and (datetime.utcnow() - member.joined_at) > dt.timedelta(days = 5) :
            await review_ping_channel.send(f'Hey {member.mention}! It would be great if you could post a review of our server on disboard :D! It helps us grow and bring new friends to the server faster ✨!!!\n https://disboard.org/review/create/1230967641200394302')
            await member.remove_roles(found_role_list)
    return

@tasks.loop(time = [dt.time(hour = 6, minute = 0, second = 0, tzinfo = dt.timezone.utc),
                    dt.time(hour = 12, minute = 0, second = 0, tzinfo = dt.timezone.utc),
                    dt.time(hour = 18, minute = 0, second = 0, tzinfo = dt.timezone.utc)])
async def bot_updatation() :
    # Called every 12 hours and does all the timed updatation that the bot needs.
    print('[LOG] Bot Updatation is under way.')
    
    guild = await bot.fetch_guild(PET_OWNER_GUILD)
    members = guild.fetch_members()
    
    # Assign levels based on people's messages.
    
    # Checks for the review ping roles
    review_ping_check(members)
    return

@bot.event
async def on_ready() :
    bot_activity = discord.Game(name = 'Getting Slapped by the slappers!', start = bot.user.created_at)
    await bot.change_presence(activity = bot_activity)
    
    print('[LOG] Beam me up scotty ;)')
    
    try :
        bot_owner = bot.get_user(BOT_OWNER_ID)
        if bot_owner.dm_channel == None :
            await bot_owner.create_dm()
        await bot_owner.dm_channel.send('Sallie the salamander has been deployed at {utc_time}'.format(utc_time = datetime.utcnow().strftime(datetime_date_format)))
    except :
        print('[on_ready func]: Ready action notif couldn\'t be sent to Sallie\'s Pet owner.')
    return

@bot.event
async def on_message(message) :
    global voice_client, HELP_DICT, SLAPPING_SALAMANDER_SERVER_ACCENT
    
    print(f'[MESSAGE LOG]: {message.author} | {message.content}')
    if message.interaction != None :
        print(f'INTERACTION DETECTED SEXY BOI {message.interaction.user.name} | {message.interaction.name}')
        
        if message.interaction.name == 'bump' :
            await message.channel.send(f'HEY THANKS {message.interaction.user.mention} FOR BUMPING MAN, I DETECTED IT CUZ YOU ARE SO SEXY!!!')
            bump_count = firebase_db_obj.child('bump').child('count').child(message.author.id).get()
            print(type(bump_count), bump_count)
            if bump_count == None :
                bump_count = 0
            else :
                bump_count = bump_count.val()
            firebase_db_obj.child('bump').child('count').child(message.author.id).set(bump_count + 1)
        return
        
    if message.content.lower() == '$$ping' :
        await message.channel.send('Bot has been successfully pinged({} ms)! tyy <33~'.format(round((bot.latency * 1000), 2)))
    if message.content.lower().startswith('$$help') :
        query = message.content.lower()[len('$$help') : ].strip()
        if query != '' :
            if query not in HELP_DICT :
                await message.channel.send('The query provided is invalid, there is no such command or cog available for sallie!')
            else :
                help_data = HELP_DICT[query]
                embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), title = help_data[0], description = help_data[1])
                await message.channel.send(embed = embed)
        else :
            embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), title = 'Sallie-Help', description = 'Sallie is here to help ya play with her :D! Heres a list of things sallie can do:')
            for query, query_data in HELP_DICT.items() :
                name, desc = query_data
                desc = desc if len(desc) <= 1024 else desc[ : 1024]
                embed.add_field(name = name, value = desc, inline = False)
                continue
            await message.channel.send(embed = embed)
    if message.content.lower() == '$$slap' :
        await message.channel.send(':lizard: :wave::skin-tone-1: *You slapped sallie gently and gained some slapping experience!!* Keep slapping dem cheeks you slappy boi!')
        slap_count = firebase_db_obj.child('slap').child('count').child(message.author.id).get()
        print(type(slap_count), slap_count)
        if slap_count.val() == None :
            slap_count = 0
        else :
            slap_count = slap_count.val()
        firebase_db_obj.child('slap').child('count').child(message.author.id).set(slap_count + 1)
        return
    if message.content.startswith('$$confess ') :
        confession = message.content[len('$$confess') : ]
        embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), title = 'Anonymous Confession', description = confession)
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