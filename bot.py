# -*- coding: utf-8 -*-
"""
Created on Tue May 21 20:02:05 2024

@author: ketch
"""

ENVIRONMENT_TYPE = 'DEV'
# ENVIRONMENT_TYPE = 'PROD'
print(f'STARTING SALLIE BOT CODE IN {ENVIRONMENT_TYPE} MODE.')

import nest_asyncio
nest_asyncio.apply()

import discord, pyrebase, os, asyncio, flask, sys, secrets, random, io, re, math
from discord.ext import tasks
from gtts import gTTS
from flask import Flask, render_template, redirect, url_for, request, make_response, session
from datetime import datetime
from threading import Thread
from markupsafe import escape
from PIL import Image, ImageDraw, ImageFont, ImageOps

import datetime as dt
import ratelimit_handler as rh
import matplotlib.pyplot as plt

# ---
os.environ['PATH'] = os.environ['PATH'] + ';' + os.path.abspath('assets')
import ffmpeg

# ----

# shorthand for the class whose __del__ raises the exception
_BEL = asyncio.base_events.BaseEventLoop

_original_del = _BEL.__del__

def _patched_del(self):
    try:
        # invoke the original method...
        _original_del(self)
    except:
        # ... but ignore any exceptions it might raise
        # NOTE: horrible anti-pattern
        pass

# replace the original __del__ method
_BEL.__del__ = _patched_del

# ----

_Task_Class = asyncio.Task

_original_del = _Task_Class.__del__

def _patched_del(self):
    try:
        # invoke the original method...
        _original_del(self)
    except:
        # ... but ignore any exceptions it might raise
        # NOTE: horrible anti-pattern
        pass

# replace the original __del__ method
_Task_Class.__del__ = _patched_del

# ---

datetime_date_format = '%a %d %b %Y, %I:%M:%S %p UTC time'
SLAPPING_SALAMANDER_SERVER_ACCENT = '#F05E22'
CACHE_RETENTION_DURATION = 1 # 1 day[in days]
ACTIVITY_INDEX_DB_CACHING_DURATION = 1 # 1 hour[in hours]
STATUS_ROTATION_DURATION = 10 # 10 mins[in minutes]
DESIRED_TICK_NUM = 10
BOT_STATUSES = ['Getting Slapped by the slappers!', # OG message!
                'Being taught cuteness and good manners by mama cc~ ✨😊🌸!', # CC
                'Drinking beer and getting horny with aya auntie~~ ehe :3 🍻', # AYA
                'Having fun learning how to code from dada adi 🧡💻!!', # ME
                'Learning how to be an alpha and an ekitten at the same time, thanks to my cute emilie auntie 🩷!!!', # Alpha Ekitten
                'Tearing off people\'s diapers and learning the ways of sexting with diapaking himself~! 🩲', # Diapaking
                'Sipping some good ol\' coffee with my lovely old granny aunt dex 💜~', # Dex
                'Grinding some demons on geometry dash, yesh! yesh! Dada taught me hehe~', # GD Reference
                'Woosh! if you read this, may you have an awesome day, mwah! 🦎', # Random cute status
                'Listening to some linkin park songs with auntie liv ❤️, shes so hot!!', # LIV
                'Reading some books reawwy carefully with reading ekitten in da slapping salamanders serva library~! 💛', # Reading Ekitten
                'Giving tons of huggies to rat auntie as I hold her hand and guide her way through the tough times~! 💙', # RAT
              ]
SPAM_CHANNEL_ID = 1245681028178251818
AUDIT_LOGS_CHANNEL_ID = 1230975925487927349
CONFESSION_CHANNEL_ID = 1239309061585899572
BOOSTER_NOTIF_CHANNEL_ID = 1269368301256179772
SALLIE_DM_LOG_CHANNEL_ID = 1327052773673664605
BOOSTER_TIER_ROLE_IDS = {'1': 1269733606432051210,
                         '2': 1269733728025055334,
                         '3': 1269733769619701902,
                         '++': 1269733864637595670,}
BOT_OWNER_ID = 568446269610000385
BOT_SELF_USER_ID = 1231274952968372317
PET_OWNER_GUILD = 1230967641200394302

HELP_DICT = {
            'ping': ['$$ping', 'Pong! Returns the ping in milliseconds for the bot.'],
            'help': ['$$help <optional:query>', 'Provided with a list of all commands available, if the optionary query is provided then it describes the command being queried.'],
            'slap': ['$$slap', 'Slaps sallie and rewards you with exp points(W.I.P.)'],
            'confess': ['$$confess <confession>', 'Posts an anonymous confession message in the confessions channel of the server with the content provided, can be used via DMs as well.'],
            'vc_connect': ['$$vc_connect', 'Connects to the same VC as the user who executed the command.'],
            'vc_disconnect': ['$$vc_disconnect', 'Disconnects from any VC that she might be in.'],
            'tts' : ['$$tts <message>', 'Converts the message from text to speech and plays it in VC.'],
            'lb': ['$$lb <counter-type:slap|bump|welcome|boost|levels>', 'Displays the leaderboards for the given counter-type.'],
            'revive': ['$$revive @person1 @person2 ...', 'Sends a sweet revival message to whoever is pinged in their DMs.'],
            'my_discord_id': ['$$my_discord_id', 'Displays the user\'s discord id. Can be used for logging into the website!'],
            'rank': ['$$rank @member', 'Sends back a rank card for the member pinged, if no user is pinged it sends the rank card for the command user.'],
            'level': ['$$level @member', 'Alias for $$rank, Sends back a rank card for the member pinged, if no user is pinged it sends the rank card for the command user.'],
            'website': ['$$website', 'Displays the URL for the home page of the server website!'],
            'server_website': ['$$server_website', 'Alias for $$website, displays the URL for the homepage of the server website!'],
            'activity_index': ['$$activity_index <hours>h <minutes>m <seconds>s', 'Looks back into it\'s message cache as queried by the user, using the lookback duration arguments, and calculates the activity index.'],
            'activity_chart': ['$$activity_chart <mode: h/m/s> {optional -g tag for grid enabling} <hours>h <minutes>m <seconds>s', 'Generates a chart based on the cached activity index for the given specifications.'],
            'activity_graph': ['$$activity_graph <mode: h/m/s> {optional -g tag for grid enabling} <hours>h <minutes>m <seconds>s', 'Alias for $$activity_chart, Generates a graph based on the cached activity index for the given specifications.'],
            'boost[ADMIN ONLY]': ['$$boost @booster', 'Updates the database to store the pinged member as a booster.[ADMIN ONLY]'],
            'echo[ADMIN ONLY]': ['$$echo #channel-mention <content>', 'Sends a message with the content specified, in the channel mentioned.[ADMIN ONLY]'],
            'echo_dm[ADMIN ONLY]': ['$$echo_dm @member-mention <content>', 'Sends a message with the content specified, in the dms of the member mentioned.[ADMIN ONLY]'],
            'echo_reply[ADMIN ONLY]': ['$$echo_reply #channel-mention <message-id> <content>', 'Replies to the message corresponding the message id specified, with the content specified, in the channel mentioned.[ADMIN ONLY]'],
            'echo_react[ADMIN ONLY]': ['$$echo_react #channel-mention <message-id> <emoji>', 'Reacts to the message corresponding the message id specified, with the reaction provided, in the channel mentioned.[ADMIN ONLY]'],
            'debug_get[ADMIN ONLY]': ['$$debug_get <variable-name>', 'Displays the current value of the variable within the running code, if the variable exists in it, if it doesn\'t then notifies the same.'],
            'debug_set[ADMIN ONLY]': ['$$debug_set <variable-name>=<value>', 'Sets the value of the mentioned global variable to the provided value, USE WITH IMMENSE CAUTION.'],
            }

FFMPEG_OPTIONS = {'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options' : '-vn'}

# -------

BOT_READY, DB_READY = False, False
BOT_START_TIME = datetime.now(dt.UTC) #.strftime(datetime_date_format)

L_OTPs, R_OTPs = {}, {}

#---------DATABASE SETUP----------
# Initializes the configurations for the firebase realtime database.
FIREBASE_API_KEY = os.environ['FIREBASE_API_KEY']

database_config = {          
                    "apiKey" : FIREBASE_API_KEY,
                    "authDomain" : "sallie-b93a6.firebaseapp.com",
                    "databaseURL" : "https://sallie-b93a6-default-rtdb.firebaseio.com",
                    "projectId" : "sallie-b93a6",
                    "storageBucket" : "sallie-b93a6.appspot.com",
                  }

firebase_client = pyrebase.initialize_app(database_config) # Intializes the firebase client object.
firebase_db_obj = firebase_client.database() # Initializes the firebase database object.

DB_READY = True
#---------------------------------

intents = discord.Intents.all()
bot = discord.Client(intents = intents)

ratelimiter = rh.RateLimiter(unit_time = 5000, default_rl = 1)

large_font = ImageFont.truetype(font = 'assets/arial.ttf', size = 25)
small_font = ImageFont.truetype(font = 'assets/arial.ttf', size = 15)

voice_client = None
activity_index_cache = []
LEVELUP_TIMES = {}
current_bot_status = BOT_STATUSES[0]

get_summation_func = lambda func : lambda x : sum([func(k) for k in range(x + 1)])
level_func = lambda x : (5 * (x ** 2)) + (50 * x) + 100
level_summation_func = get_summation_func(level_func)

def calculate_level(xp, lvl_func) :
    lvl = 0
    needed = lvl_func(0)
    while xp >= needed :
        xp -= needed
        lvl += 1
        needed = lvl_func(lvl)
        continue
    return lvl

def get_font(content_length) :
    font_size = 25
    letter_capacity = 14
    while letter_capacity < content_length :
        font_size -= 1
        letter_capacity += 1.1
        continue
    font = ImageFont.truetype(font = 'assets/arial.ttf', size = font_size)
    return font

def get_datetime_str(do) :
    return do.strftime(datetime_date_format)

def get_datetime_obj(ds) :
    return datetime.strptime(ds, datetime_date_format).replace(tzinfo = dt.UTC)

activity_index_db_upload_time = get_datetime_str(datetime.now(dt.UTC))
status_rotation_time = get_datetime_str(datetime.now(dt.UTC))

async def fetch_invite_data(guild = None) :
    guild = guild or bot.get_guild(PET_OWNER_GUILD) or (await bot.fetch_guild(PET_OWNER_GUILD))
    invites = await guild.invites()
    invite_data = {}
    for invite in invites :
        invite_data[invite.code] = {'inviter_id' : invite.inviter.id,
                                    'inviter_name' : invite.inviter.name,
                                    'uses' : invite.uses}
        continue
    return invite_data

async def sync_db_invite_cache() :
    firebase_db_obj.child('invite_cache').child('empty').set({})
    
    guild = bot.get_guild(PET_OWNER_GUILD) or (await bot.fetch_guild(PET_OWNER_GUILD))
    invites = await guild.invites()
    
    for invite in invites :
        invite_info = {'inviter_id' : invite.inviter.id,
                       'inviter_name' : invite.inviter.name,
                       'uses' : invite.uses}
        firebase_db_obj.child('invite_cache').child(invite.code).set(invite_info)
        continue
    return

async def review_ping_check_iteration(member, review_ping_channel) :
    REVIEW_PING_ROLE_ID = 1242796399754743808
    
    found_role_list = [role for role in member.roles if role.id == REVIEW_PING_ROLE_ID]
    print(f'[LOG] Review availability is being examined for {member.name} right now... {True if any(found_role_list) else False} {(datetime.now(dt.UTC).astimezone(dt.timezone.utc) - member.joined_at)}')
    if any(found_role_list) and (datetime.now(dt.UTC).astimezone(dt.timezone.utc) - member.joined_at) > dt.timedelta(days = 5) :
        await review_ping_channel.send(f'Hey {member.mention}! It would be great if you could post a review of our server on disboard :D! It helps us grow and bring new friends to the server faster ✨!!!\n https://disboard.org/review/create/1230967641200394302')
        
        if member.dm_channel == None :
            await member.create_dm()
        try :
            await member.dm_channel.send('Hii!! Sallie this side ^^! You stopped slapping me :<! Me and the others really miss you :3 will you take some time to visit our server again? It\'d make us all soo happy :D!! ' + review_ping_channel.mention)
        except Exception as e :
            print(e)
            await review_ping_channel.send(f'{member.mention} you are a FAT ASS BITCH for blocking me hmpf~! FUCK YOU! Why are you even in the server if you\'re never gonna talk?')
        
        # await member.remove_roles(*found_role_list)
    return

async def review_ping_check(members) :
    print('[LOG] Review ping check is under way.')
    REVIEW_PING_CHANNEL_ID = 1242796180359086130
    
    review_ping_channel = await bot.fetch_channel(REVIEW_PING_CHANNEL_ID)
    for member in members :
        ratelimited_iteration = ratelimiter.handle(func = review_ping_check_iteration, default_rl = 1)
        await ratelimited_iteration(member, review_ping_channel)
        continue
    return

# @tasks.loop(time = [dt.time(hour = 6, minute = 0, second = 0, tzinfo = dt.timezone.utc),
#                     dt.time(hour = 12, minute = 0, second = 0, tzinfo = dt.timezone.utc),
#                     dt.time(hour = 18, minute = 0, second = 0, tzinfo = dt.timezone.utc)])
@tasks.loop(hours = 12)
async def bot_updatation() :
    # Called every 12 hours and does all the timed updatation that the bot needs.
    print('[LOG] Bot Updatation is under way.')
    
    guild = await bot.fetch_guild(PET_OWNER_GUILD)
    members = [member async for member in guild.fetch_members()]
    
    # Assign levels based on people's messages.
    
    # Checks for the review ping roles
    await review_ping_check(members)
    return

@bot.event
async def on_ready() :
    global BOT_OWNER_ID, BOT_READY, BOT_START_TIME, activity_index_cache, activity_index_db_upload_time, current_bot_status, status_rotation_time

    current_bot_status = BOT_STATUSES[0]
    bot_activity = discord.Game(name = current_bot_status, start = bot.user.created_at)
    await bot.change_presence(activity = bot_activity)

    status_rotation_time = get_datetime_str(datetime.now(dt.UTC) + dt.timedelta(minutes = STATUS_ROTATION_DURATION))
    
    print('[LOG] Beam me up scotty ;)')
    
    try :
        bot_owner = bot.get_user(BOT_OWNER_ID)
        if bot_owner.dm_channel == None :
            await bot_owner.create_dm()
        await bot_owner.dm_channel.send('Sallie the salamander has been deployed at {utc_time}'.format(utc_time = datetime.now(dt.UTC).strftime(datetime_date_format)))
    except :
        print('[on_ready func]: Ready action notif couldn\'t be sent to Sallie\'s Pet owner.')
    
    if ENVIRONMENT_TYPE == 'PROD' :
        bot_updatation.start()
    
    await sync_db_invite_cache()

    # Syncing activity_index_cache
    activity_index_cache = firebase_db_obj.child('activity_index_cache').get().val() or []
    activity_index_db_upload_time = get_datetime_str(datetime.now(dt.UTC) + dt.timedelta(hours = ACTIVITY_INDEX_DB_CACHING_DURATION))
    
    BOT_READY = True
    BOT_START_TIME = datetime.now(dt.UTC)
    return

@bot.event
async def on_resume() :
    if not bot_updatation.is_running() and ENVIRONMENT_TYPE == 'PROD' :
        bot_updatation.start()
    
    await sync_db_invite_cache()
    
    BOT_START_TIME = datetime.now(dt.UTC)
    return

@bot.event
async def on_invite_create(invite) :
    invite_info = {'inviter_id' : invite.inviter.id,
                   'inviter_name' : invite.inviter.name,
                   'uses' : invite.uses}
    
    firebase_db_obj.child('invite_cache').child(invite.code).set(invite_info)
    
    audit_logs_channel = bot.get_channel(AUDIT_LOGS_CHANNEL_ID)
    await audit_logs_channel.send(f'[INVITE CREATION LOG]: An invite was created by {invite.inviter.name}.')
    await sync_db_invite_cache()
    return

@bot.event
async def on_invite_delete(invite) :
    invite_cache = firebase_db_obj.child('invite_cache').get()
    
    if invite_cache == None : return
    if invite.code not in invite_cache.val() : return
    
    invite_info = firebase_db_obj.child('invite_cache').child(invite.code).get().val()
    firebase_db_obj.child('invite_cache').child(invite.code).remove()
    
    audit_logs_channel = bot.get_channel(AUDIT_LOGS_CHANNEL_ID)
    await audit_logs_channel.send(f'[INVITE DELETION LOG]: An invite by {invite_info["inviter_name"]} was deleted.')
    await sync_db_invite_cache()
    return

@bot.event
async def on_member_join(member) :
    guild = bot.get_guild(PET_OWNER_GUILD) or (await bot.fetch_guild(PET_OWNER_GUILD))
    
    # welcome stuff..
    
    # ---
    # invite stuff..
    
    audit_logs_channel = bot.get_channel(AUDIT_LOGS_CHANNEL_ID)
    
    invites_cache = firebase_db_obj.child('invite_cache').get().val()
    updated_invites = await fetch_invite_data(guild)
    
    for code, info in updated_invites.items() :
        if info['uses'] > invites_cache[code]['uses'] :
            # .. this is the invite used to join.
            await audit_logs_channel.send(f'[INVITATION DETECTION LOGS]: {member.name} was invited by {info["inviter_name"]}.')
            break
        continue
    
    await sync_db_invite_cache()
    return

@bot.event
async def on_raw_member_remove(member) :
    # remove all their data from the database.
    return
# --------------------------------------

def fetch_counter_data(counter_type) :
    global firebase_db_obj
    
    if counter_type not in ['bump', 'slap', 'boost', 'welcome'] : return {}
    data = {}
    
    salaslappers = firebase_db_obj.child(counter_type).get()
    for salaslapper, salaslapper_data in salaslappers.val().items() :
        data[salaslapper_data['username']] = salaslapper_data['count'] if 'count' in salaslapper_data else 0
        continue
    return data

def fetch_level_data() :
    global firebase_db_obj
    
    data = {}
    
    salaslappers = firebase_db_obj.child('levels').get()
    for salaslapper, salaslapper_data in salaslappers.val().items() :
        data[salaslapper_data['username']] = {'xp': salaslapper_data['xp'] if 'xp' in salaslapper_data else 0, 
                                              'level': salaslapper_data['level'] if 'level' in salaslapper_data else 0}
        continue
    return data

def fetch_counter_leaderboard_str(counter_type) :
    # LEVEL COUNTER NOT INCLUDED.
    data = fetch_counter_data(counter_type)
    
    leaderboard_str = ''
    
    rank = 0
    for data_key in sorted(data, key = data.get, reverse = True) :
        leaderboard_str += f'{rank}.{data_key}: {data[data_key]} pts\n'
        rank += 1
        continue
    return leaderboard_str

# --------------------------------------

# -------------------------------
app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

def get_login_info() :
    is_logged_in = session.get('logged_in?') or 'no'
    if is_logged_in == 'yes' :
        return {'logged_in?': is_logged_in, 'discord_id': session['discord_id'], 'username': session['username'], 'avatar': session['avatar']}
    elif is_logged_in == 'no' :
        session['logged_in?'] = 'no'
        return {'logged_in?': 'no'}

@app.route('/')
def main() :
    return redirect(url_for('ss_landing_home_page'))

@app.route('/cookies/theme', methods = ['POST', 'GET'])
def theme_cookies() :
    if request.method == 'POST' :
        curr_theme = request.data.decode('utf-8')
        print(curr_theme)
        sys.stdout.flush()
        
        response = make_response({'theme': curr_theme})
        response.set_cookie('theme', curr_theme, max_age = 60 * 60 * 24 * 365 * 1)
        return response
    return 'Hello ehhehe'

@app.route('/home')
def ss_landing_home_page() :
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_landing_home_page_template.html', theme = curr_theme, login_info = get_login_info())

@app.route('/info')
def ss_info_page() :
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_info_page_template.html', theme = curr_theme, login_info = get_login_info())

@app.route('/rules')
def ss_rules_page() :
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_rules_page_template.html', theme = curr_theme, login_info = get_login_info())

@app.route('/sallie_status')
def ss_sallie_bot_status_page() :
    global BOT_START_TIME
    
    deploy_time = BOT_START_TIME.strftime('%I:%M:%S %p (%Z Time)')
    deploy_date = BOT_START_TIME.strftime('%A, %d %b %Y (%Z Time)')
    curr_theme = request.cookies.get('theme') or 'light'
    
    return render_template('ss_sallie_bot_status_page_template.html', time = deploy_time, date = deploy_date, theme = curr_theme, login_info = get_login_info())

@app.route('/leaderboard')
def ss_leaderboards_main_page() :
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_leaderboards_main_page_template.html', theme = curr_theme, login_info = get_login_info())

@app.route('/leaderboard/<counter_type>')
def leaderboard_page(counter_type) :
    global BOT_READY, DB_READY
    
    if not (BOT_READY and DB_READY) :
        if not BOT_READY :
            return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, so the leaderboard data is unavailable right now.'})
        elif not DB_READY :
            return render_template('error_redirect_page_template.html', error = {'title': 'DB Startup Error', 'description': 'The database has either not started up properly or is facing some issues, please try again later.'})
        # return 'Bot is currently either starting up or undergoing some internal issues, so the leaderboard data is unavailable right now.'
    
    if counter_type not in ['bump', 'slap', 'boost', 'welcome', 'levels'] :
        return render_template('error_redirect_page_template.html', error = {'title': 'Invalid Leaderboard Error', 'description': 'Whoops you are looking for the leaderboard of something that doesn\'t exist!'})
        # return 'Whoops you are looking for the leaderboard of something that doesn\'t exist!'
    
    if counter_type == 'levels' :
        raw_data = fetch_level_data()
        data = []
        rank = 1
        for data_key in sorted(raw_data, key = lambda k: raw_data.get(k)['xp'], reverse = True) :
            data.append({'rank': rank, 'username': data_key, 'count': raw_data[data_key]['level']})
            rank += 1
            continue
    else :
        raw_data = fetch_counter_data(counter_type)
        data = []
        rank = 1
        for data_key in sorted(raw_data, key = raw_data.get, reverse = True) :
            data.append({'rank': rank, 'username': data_key, 'count': raw_data[data_key]})
            rank += 1
            continue
    return render_template('leaderboard_page_template.html', counter_type = counter_type.title(), data = data)

@app.route('/login')
def ss_login_page() :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to login with a new one.'})
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_login_page_template.html', theme = curr_theme, login_info = get_login_info())

@app.route('/login/username/verify', methods = ['POST', 'GET'])
def login_username_verification() :
    if session.get('logged_in?') == 'yes' :
        response = make_response({'status': 'failure', 'error': 'You are already logged into an account, logout before trying to login with a new one.'})
        return response
    
    global BOT_READY, DB_READY, firebase_db_obj
    
    if not BOT_READY :
        response = make_response({'status': 'failure', 'error': 'Bot is currently either starting up or undergoing some internal issues, Username validation is not possible at the moment.'})
        return response
    
    if not DB_READY :
        response = make_response({'status': 'failure', 'error': 'The database has either not started up properly or is facing some issues, please try again later.'})
        return response
    
    if request.method == 'POST' :
        typed_info = request.get_json()
        print(typed_info)
        sys.stdout.flush()
        username, password = typed_info['username'], typed_info['password']
        
        accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
        if str(username) in [str(account) for account in list(accounts.keys())] :
            account_info = accounts[username]
            if account_info['password'] == password :
                response = make_response({'status': 'success'})
            else :
                response = make_response({'status': 'failure', 'error': 'Invalid password!'})
            return response
        else :
            response = make_response({'status': 'failure', 'error': 'Account with that username does not exist.'})
            return response
    
    response = make_response({'status': 'failure', 'error': 'Something unexpected has occurred, please contact admin or staff for help with this.'})
    return response

async def dm_logging_user(discord_id) :
    global bot, PET_OWNER_GUILD
    
    await bot.wait_until_ready()
    
    try :
        logging_user = bot.get_user(discord_id)
    except :
        return False, {'title': 'User Not Found Error', 'description': 'The discord ID provided is either invalid or could not be found. Please contact server admin and staff if you think the ID is correct.'}
    
    if not any([guild.id == PET_OWNER_GUILD for guild in logging_user.mutual_guilds]) :
        return False, {'title': 'Not in Server Error', 'description': 'The bot cannot find you in the server and thus the OTP request has been cancelled.'}
    
    try :
        if logging_user.dm_channel == None :
            await logging_user.create_dm()
        await logging_user.dm_channel.send(f'The OTP(One Time Password)/Secret Key for you to login to your account is given below: ```{L_OTPs[discord_id]["OTP"]}``` To login you must copy this and paste it on the page as instructed. If you have not tried logging into your account and are seeing this message, contact the server staff immediately as this might be a security issue!')
        return True, {}
    except Exception as e :
        print(e)
        sys.stdout.flush()
        return False, {'title': 'DM Error', 'description': 'Could not DM the OTP to the discord account provided.'}

@app.route('/login/username/<string:username>')
def ss_login_username_otp_page(username) :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to login with a new one.'})
    global BOT_READY
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, OTP generation is not possible at the moment.'})
    
    # ----
    global L_OTPs, bot, PET_OWNER_GUILD
    
    accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
    account_info = accounts.get(username)
    if account_info == None :
        return render_template('error_redirect_page_template.html', error = {'title': 'Invalid Account Info Error', 'description': 'No account with the provided username and password exists, please register first, or use the discord id method to login. If you feel like this is an issue on the website\'s end please contact admin and staff about this for further help. Thanks!'})
        pass
    discord_id = account_info['discord_id']
    
    L_OTPs[discord_id] = {'OTP': secrets.token_hex(32), 'login_method': 'username', 'username': username, 'discord_id': discord_id} # As per current standards 32 bytes is the amount of bytes worth of data that is safe enough.
    
    dm_attempt_task = bot.loop.create_task(dm_logging_user(discord_id))
    
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_login_otp_page_template.html', theme = curr_theme, discord_id = discord_id)

@app.route('/login/otp/<int:discord_id>')
def ss_login_otp_page(discord_id) :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to login with a new one.'})
    global BOT_READY
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, OTP generation is not possible at the moment.'})
    
    # ----
    global L_OTPs, bot, PET_OWNER_GUILD
    
    L_OTPs[discord_id] = {'OTP': secrets.token_hex(32), 'login_method': 'otp'} # As per current standards 32 bytes is the amount of bytes worth of data that is safe enough.
    
    dm_attempt_task = bot.loop.create_task(dm_logging_user(discord_id))
    
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_login_otp_page_template.html', theme = curr_theme, discord_id = discord_id)

def login_without_username(discord_id) :
    global L_OTPs, bot
    
    discord_user = bot.get_user(discord_id)
    discord_username = discord_user.name
    discord_avatar = discord_user.avatar.url if discord_user.avatar else None
    
    session['discord_id'] = discord_id
    session['username'] = discord_username or f'({str(discord_id)})th salamander'
    session['avatar'] = discord_avatar or url_for('static', filename='default_account_pfp.png')
    
    # Uses the username stored in database if the user has registered in the past.
    accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
    stored_usernames = [k for k, v in accounts.items() if v['discord_id'] == session['discord_id']]
    if any(stored_usernames) : session['username'] = stored_usernames[0]
    
    session['logged_in?'] = 'yes'
    session['login_method'] = 'otp'
    return

def login_with_username(discord_id, username) :
    global L_OTPs, bot
    
    discord_user = bot.get_user(discord_id)
    discord_username = username or discord_user.name
    discord_avatar = discord_user.avatar.url if discord_user.avatar else None
    
    session['discord_id'] = discord_id
    session['username'] = discord_username or f'({str(discord_id)})th salamander'
    session['avatar'] = discord_avatar or url_for('static', filename='default_account_pfp.png')
    
    session['logged_in?'] = 'yes'
    session['login_method'] = 'username'
    return

@app.route('/logout', methods = ['POST', 'GET'])
def logout() :
    if request.method == 'POST' :
        session.pop('discord_id')
        session.pop('username')
        session.pop('avatar')
        
        session['logged_in?'] = 'no'
        
        response = make_response({'status': 'success'})
        return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

@app.route('/login/otp/verify/<int:discord_id>', methods = ['POST', 'GET'])
def login_otp_verification(discord_id) :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to login with a new one.'})
    global BOT_READY
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, OTP verification is not possible at the moment.'})
    
    # ----
    global L_OTPs
    
    if request.method == 'POST' :
        typed_otp = request.data.decode('utf-8')
        print(typed_otp, discord_id, L_OTPs)
        sys.stdout.flush()
        
        if discord_id not in L_OTPs :
            response = make_response({'status': 'failure', 'error': 'OTP was never generated for this user.'})
        else :
            login_info = L_OTPs[discord_id]
            if typed_otp == login_info['OTP'] :
                # do the login here by calling a separate function that logs you in.
                if login_info['login_method'] == 'otp' :
                    login_without_username(discord_id)
                elif login_info['login_method'] == 'username' :
                    login_with_username(discord_id, login_info['username'])
                response = make_response({'status': 'success'})
            else :
                response = make_response({'status': 'failure', 'error': 'Typed OTP is wrong.'})
        return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

@app.route('/register')
def ss_registration_page() :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_registration_page_template.html', theme = curr_theme)

@app.route('/register/discord_id_validity', methods = ['POST', 'GET'])
def discord_id_validity_check() :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    global BOT_READY, DB_READY, firebase_db_obj
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, Discord ID validation is not possible at the moment.'})
    
    if not DB_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'DB Startup Error', 'description': 'The database has either not started up properly or is facing some issues, please try again later.'})
    
    if request.method == 'POST' :
        try :
            discord_id = int(request.data.decode('utf-8'))
        except :
            response = make_response({'availability': 'unavailable'})
            return response
        
        accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
        if any([str(accounts[account]['discord_id']) == str(discord_id) for account in accounts]) :
            response = make_response({'availability': 'unavailable'})
            return response
        else :
            response = make_response({'availability': 'available'})
            return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

@app.route('/register/username_validity', methods = ['POST', 'GET'])
def username_validity_check() :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    global BOT_READY, DB_READY, firebase_db_obj
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, Username validation is not possible at the moment.'})
    
    if not DB_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'DB Startup Error', 'description': 'The database has either not started up properly or is facing some issues, please try again later.'})
    
    if request.method == 'POST' :
        username = request.data.decode('utf-8')
        
        accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
        if str(username) in [str(account) for account in list(accounts.keys())] :
            response = make_response({'availability': 'unavailable'})
            return response
        else :
            response = make_response({'availability': 'available'})
            return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

async def dm_registering_user(discord_id) :
    global bot, PET_OWNER_GUILD
    
    await bot.wait_until_ready()
    
    try :
        registering_user = bot.get_user(discord_id)
    except :
        return False, {'title': 'User Not Found Error', 'description': 'The discord ID provided is either invalid or could not be found. Please contact server admin and staff if you think the ID is correct.'}
    
    if not any([guild.id == PET_OWNER_GUILD for guild in registering_user.mutual_guilds]) :
        return False, {'title': 'Not in Server Error', 'description': 'The bot cannot find you in the server and thus the OTP request has been cancelled.'}
    
    try :
        if registering_user.dm_channel == None :
            await registering_user.create_dm()
        await registering_user.dm_channel.send(f'The OTP(One Time Password)/Secret Key for you to register your account is given below: ```{R_OTPs[discord_id]["OTP"]}``` To register your account successfully, you must copy this and paste it on the page as instructed. If you have not tried registering your account and are seeing this message, contact the server staff immediately as this might be a security issue!')
        return True, {}
    except Exception as e :
        print(e)
        sys.stdout.flush()
        return False, {'title': 'DM Error', 'description': 'Could not DM the OTP to the discord account provided.'}

@app.route('/register/info_upload', methods = ['POST', 'GET'])
def registration_info_upload() :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    global BOT_READY, DB_READY, firebase_db_obj
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, OTP generation is not possible at the moment.'})
    
    if not DB_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'DB Startup Error', 'description': 'The database has either not started up properly or is facing some issues, please try again later.'})
    
    # ----
    if request.method == 'POST' :
        global R_OTPs, bot, PET_OWNER_GUILD
        
        reg_info = request.get_json()
        try :
            discord_id = int(reg_info['discord_id'])
        except :
            response = make_response({'status': 'failure', 'error': 'Invalid Discord ID entered.'})
            return response
        
        accounts = firebase_db_obj.child('website').child('accounts').get().val() or {}
        if any([str(accounts[account]['discord_id']) == str(discord_id) for account in accounts]) :
            response = make_response({'status': 'failure', 'error': 'An account already exists for the discord account linked to this discord ID.'})
            return response
        if str(reg_info['username']) in [str(account) for account in list(accounts.keys())] :
           response = make_response({'status': 'failure', 'error': 'An account with this username already exists.'})
           return response
        
        R_OTPs[discord_id] = {'OTP': secrets.token_hex(32), 'username': reg_info['username'], 'password': reg_info['password']} # As per current standards 32 bytes is the amount of bytes worth of data that is safe enough.
        
        dm_attempt_task = bot.loop.create_task(dm_registering_user(int(discord_id)))
        response = make_response({'status': 'success'})
        return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

@app.route('/register/otp/<int:discord_id>')
def ss_register_otp_page(discord_id) :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    curr_theme = request.cookies.get('theme') or 'light'
    return render_template('ss_registration_otp_page_template.html', theme = curr_theme, discord_id = discord_id)

def register(discord_id) :
    global R_OTPs, firebase_db_obj
    
    reg_info = R_OTPs[discord_id]
    
    firebase_db_obj.child('website').child('accounts').child(reg_info['username']).child('discord_id').set(discord_id)
    firebase_db_obj.child('website').child('accounts').child(reg_info['username']).child('password').set(reg_info['password'])
    
    discord_user = bot.get_user(discord_id)
    discord_username = discord_user.name
    discord_avatar = discord_user.avatar.url if discord_user.avatar else None
    
    session['discord_id'] = discord_id
    session['username'] = reg_info['username'] or discord_username or f'({str(discord_id)})th salamander'
    session['avatar'] = discord_avatar or url_for('static', filename='default_account_pfp.png')
    
    session['logged_in?'] = 'yes'
    return

@app.route('/register/otp/verify/<int:discord_id>', methods = ['POST', 'GET'])
def register_otp_verification(discord_id) :
    if session.get('logged_in?') == 'yes' :
        return render_template('error_redirect_page_template.html', error = {'title': 'Already logged In Error', 'description': 'You are already logged into an account, logout before trying to register a new one.'})
    global BOT_READY, DB_READY
    
    if not BOT_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'Bot Startup Error', 'description': 'Bot is currently either starting up or undergoing some internal issues, OTP verification is not possible at the moment.'})
    
    if not DB_READY :
        return render_template('error_redirect_page_template.html', error = {'title': 'DB Startup Error', 'description': 'The database has either not started up properly or is facing some issues, please try again later.'})
    
    # ----
    global R_OTPs
    
    if request.method == 'POST' :
        typed_otp = request.data.decode('utf-8')
        print(typed_otp, discord_id, R_OTPs)
        sys.stdout.flush()
        
        if discord_id not in R_OTPs :
            response = make_response({'status': 'failure', 'error': 'OTP was never generated for this discord ID.'})
        else :
            if typed_otp == R_OTPs[discord_id]['OTP'] :
                # do the registration here by calling a separate function that registers you.
                register(discord_id)
                response = make_response({'status': 'success'})
            else :
                response = make_response({'status': 'failure', 'error': 'Typed OTP is wrong.'})
        return response
    return render_template('error_redirect_page_template.html', error = {'title': 'Unknown Error', 'description': 'Something unexpected has occurred, please contact admin or staff for help with this.'})

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

async def on_boost(booster) :
    # Notify about it to people on the server.
    boost_notif_channel = bot.get_channel(BOOSTER_NOTIF_CHANNEL_ID)
    if boost_notif_channel == None :
        boost_notif_channel = await bot.fetch_channel(BOOSTER_NOTIF_CHANNEL_ID)
    
    boost_notif_embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), 
                                      title = f'♡ __{booster.name} just boosted the server!__',
                                      description = 'Thanks so much for boosting our server yay!!')
    boost_notif_embed.set_thumbnail(url = 'https://media.discordapp.net/attachments/1230975895213441034/1269723474923094110/images.png?ex=66b119a2&is=66afc822&hm=e154d18c3935830b2d57343bba2642561d1b43705ab2b341cb538579da1ac2ae&=&format=webp&quality=lossless&width=450&height=252')
    await boost_notif_channel.send(embed = boost_notif_embed)
    
    name = firebase_db_obj.child('boost').child(booster.id).child('username').get().val()
    count = firebase_db_obj.child('boost').child(booster.id).child('count').get().val() or 0
    tier = firebase_db_obj.child('boost').child(booster.id).child('tier').get().val() or '0'
    
    print(name, count, tier)
    
    prev_tier = tier
    
    count += 1
    if tier != '++' :
        if int(tier) < 3 :
            tier = str(int(tier) + 1)
        else :
            tier = '++'
    else :
        tier = '++'
    
    # Changing up roles
    guild = bot.get_guild(PET_OWNER_GUILD)
    if guild == None :
        guild = await bot.fetch_guild(PET_OWNER_GUILD)
    if prev_tier != '0' :
        old_tier_role = guild.get_role(BOOSTER_TIER_ROLE_IDS[prev_tier])
        await booster.remove_roles(old_tier_role)
    
    new_tier_role = guild.get_role(BOOSTER_TIER_ROLE_IDS[tier])
    await booster.add_roles(new_tier_role)
    
    if prev_tier != '++' :
        boost_tier_notif_embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), 
                                               title = f'♡ __{booster.name} just got a Tier Upgrade!!__',
                                               description = f'Congrats! Your new boost tier is Tier {tier}!')
        boost_tier_notif_embed.set_thumbnail(url = 'https://media.discordapp.net/attachments/1230975895213441034/1269723474923094110/images.png?ex=66b119a2&is=66afc822&hm=e154d18c3935830b2d57343bba2642561d1b43705ab2b341cb538579da1ac2ae&=&format=webp&quality=lossless&width=450&height=252')
        await boost_notif_channel.send(embed = boost_tier_notif_embed)
    
    firebase_db_obj.child('boost').child(str(booster.id)).child('username').set(booster.name)
    firebase_db_obj.child('boost').child(str(booster.id)).child('count').set(count)
    firebase_db_obj.child('boost').child(str(booster.id)).child('tier').set(tier)
    return

async def on_unboost(booster) :
    # ... do this in a bit
    return

def get_boost_gain(old_value, member, float_allowed = False) :
    name = firebase_db_obj.child('boost').child(member.id).child('username').get().val()
    count = firebase_db_obj.child('boost').child(member.id).child('count').get().val() or 0
    tier = firebase_db_obj.child('boost').child(member.id).child('tier').get().val() or '0'
    
    # if tier == '++' : tier = ((count - 4) * 0.1) + 4
    if tier == '++' : tier = 4
    
    if not float_allowed :
        return (old_value * (int(tier) + 1))
    return (old_value + ((int(tier) / 10) * old_value))

async def generate_rank_card(message) :
    member = message.mentions[0] if any(message.mentions) else message.author
    
    size = (109, 109)
    pfp = member.guild_avatar or member.avatar
    pfp_asset = pfp.with_size(128)
    pfp_img_data = io.BytesIO(await pfp_asset.read())
    pfp_img_obj = Image.open(pfp_img_data)
    pfp_img_obj = pfp_img_obj.resize(size)
    
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask) 
    draw.ellipse((0, 0) + size, fill = 255)
    
    output_pfp_img = ImageOps.fit(pfp_img_obj, mask.size, centering = (0.5, 0.5))
    output_pfp_img.putalpha(mask)
    
    img = Image.open('assets/rank_card_template.png')
    I1 = ImageDraw.Draw(img)
    
    level_data = firebase_db_obj.child('levels').get().val()
    print(level_data)
    sys.stdout.flush()
    # {id: {'username': ..., 'xp': ...}}
    ranked_id_list = sorted(level_data, key = lambda k : level_data.get(k)['xp'], reverse = True)
    
    member_info = level_data.get(str(member.id)) or {'username': member.name, 'xp': 0}
    member_name = member.name
    member_rank = ranked_id_list.index(str(member.id)) + 1 if str(member.id) in ranked_id_list else 'undefined'
    member_xp = member_info['xp']
    member_level = calculate_level(member_xp, level_func)
    
    I1.text((183, 44), "{member_name}".format(member_name = member_name), fill = (0, 0, 0), font = get_font(len("{member_name}".format(member_name = member_name))))
    I1.text((183, 97), "Rank: {member_rank}".format(member_rank = member_rank), fill = (0, 0, 0), font = small_font)
    member_current_lvl_xp = member_xp - level_summation_func(member_level - 1)
    print((member_current_lvl_xp), (level_func(member_level)), (33 + ((378 - 33) * (member_current_lvl_xp / level_func(member_level))), ((member_current_lvl_xp / level_func(member_level)))))
    sys.stdout.flush()
    x1 = 33 + ((378 - 33) * (member_current_lvl_xp / level_func(member_level)))
    I1.rounded_rectangle([33, 165, x1, 185], radius = 10, fill = (231, 162, 44, 230))
    I1.text((40, 166), "Level: {member_level}(XP: {xp})".format(member_level = member_level, xp = str(round((member_xp - level_summation_func(member_level - 1)), 2)) + '/' + str(round(level_func(member_level), 2))), fill = (0, 0, 0), font = small_font)
    
    _, _, _, pfp_mask = output_pfp_img.split()
    img.paste(output_pfp_img, (36, 28), pfp_mask)
    
    sallie_overlay_img = Image.open('assets/rank_card_template_overlay.png').convert('RGBA')
    img.paste(sallie_overlay_img, (0, 0), mask = sallie_overlay_img)
    
    with io.BytesIO() as image_binary :
        img.save(image_binary, 'PNG')
        image_binary.seek(0)
        await message.channel.send(file = discord.File(fp = image_binary, filename = 'image.png'))
    return

async def run_defamer_check(message) :
    # Checks to see if the person who sent the message is trying to defame the server owner.
    owner_aliases = ['owner', 'adi', 'dead server owner', 'typedecker', 'decker']
    defamation_words = ['pedo', 'pedophile', 'rape']
    defamation_phrases = ['owner is a pedo', 'owner is a pedophile', 'pedo owner', 'pedophile owner', 'typedecker is a pedo', 'pedo typedecker', 'pedo decker', 'typedecker is a pedophile', 'pedophile typedecker']
    
    danger_index = 0 # the higher the index's value the higher the danger posed by the person writing that message.
    
    danger_index += 0.1 * len([alias for alias in owner_aliases if alias in message.content])
    danger_index += 0.7 * len([word for word in defamation_words if word in message.content])
    
    if (any([alias for alias in owner_aliases if alias in message.content]) and any([word for word in defamation_words if word in message.content])) :
        danger_index += 5.0
    
    danger_index += 100.0 * len([phrase for phrase in defamation_phrases if phrase in message.content])
    
    guild = bot.get_guild(PET_OWNER_GUILD)
    if guild == None :
        guild = await bot.fetch_guild(PET_OWNER_GUILD)
    
    # if guild.is_dm_spam_detected(): danger_index += 4.0
    # if guild.is_raid_detected(): danger_index += 4.0
    
    # DANGER BASED ACTION.
    # * danger < 5: Alert mods in the channel and in dms about it.
    # * danger == 5: Alert mods in the channel and in dms and time the person out.
    # * danger > 5: Alert mods in channel and dms and Ban the person who said it.
    
    # MOD_ROLE_ID = 
    if danger_index < 5 :
        # ...
        pass
    return

def _welcome_calculate_decay_with_sharp_drop(time_diff: dt.timedelta):
    """
    Calculate points with an initial gradual decay and a drastic drop after 5 minutes.
    """
    seconds = time_diff.total_seconds()
    minutes = seconds / 60
    
    # If time_diff exceeds 1 day, return 1.0
    if seconds >= 86400:  # 24 hours
        return 1.0
    
    # Parameters for the decay
    scale = 5  # Maximum points for very short durations
    initial_decay_rate = 0.5  # Slow decay for durations before 5 minutes
    sharp_decay_rate = 3.0  # Drastic decay for durations after 5 minutes
    threshold_minutes = 5  # Drastic decay starts after this time (in minutes)

    if minutes <= threshold_minutes:
        # Gradual decay before the threshold
        return math.ceil(scale * math.exp(-initial_decay_rate * minutes))
    
    # Drastic decay after the threshold
    adjusted_minutes = (minutes - threshold_minutes) / (1440 - threshold_minutes)  # Normalize to 1 day
    return max(1.0, math.ceil(scale * math.exp(-sharp_decay_rate * adjusted_minutes)))

async def welcome_count_check(message) :
    og_msg = await message.channel.fetch_message(message.reference.message_id) # Fetch the parent message for this reply message.

    # If the member who joined is also the one writing this message, then its not considered for point gain.
    if og_msg.author == message.author: return
    # If the parent message isn't a member join message, then this message is not a welcome message.
    if og_msg.type != discord.MessageType.new_member: return
    # If the welcome message was sent 2 weeks or later past the member's joining, it isn't counted.
    time_diff = (message.created_at - og_msg.created_at)
    if time_diff > dt.timedelta(days = 14): return

    # We categorize welcome messages into two types: stickers and text messages, both matter equally and give points. Here we figure out which type of message the current one is.
    welcome_type = 'text'
    if len(message.stickers) > 0 :
        welcome_type = 'sticker'
    else :
        welcome_type = 'text'

    # Fetch there already being a welcome message for the associated join message, of the detected type.
    pre_existence = firebase_db_obj.child('welcome_cache').child(str(message.author.id)).child(str(og_msg.id)).child(welcome_type).get().val() or False
    if pre_existence: return # If join message has already been replied to with a welcome earlier, the current message isnt considered for point gain.

    # Fetch the current value of count from the database to add onto it.
    count = firebase_db_obj.child('welcome').child(str(message.author.id)).child('count').get().val() or 0
    
    if welcome_type == 'sticker':
        # If the welcome message was merely a sticker, add one to the point count.
        firebase_db_obj.child('welcome').child(str(message.author.id)).child('count').set(count + 1)
        pass
    elif welcome_type == 'text':
        # If the welcome message was a full on text message, we give it a score based on certain aspects.
        welcome_score = 1 # +1 for just being sent.
        if any([k in message.content.lower() for k in ['welcome', 'wlcm']]):
            # +1 for including the word WELCOME or wlcm or any other synonyms.
            welcome_score += 1
        if message.content.isupper() :
            # +1 for being uppercase and excited!
            welcome_score += 1
        if '!' in message.content :
            # +1 for using exclamation marks :3
            welcome_score += 1

        # scores the message for it's quickness after the joining of the member. adds a competitive sense to the whole thing.
        welcome_score += _welcome_calculate_decay_with_sharp_drop(time_diff)

        # Updates the count variable by incrementing it by the welcome score calculated.
        firebase_db_obj.child('welcome').child(str(message.author.id)).child('count').set(count + welcome_score)
        pass

    # Set the username to the username of the message author.
    firebase_db_obj.child('welcome').child(str(message.author.id)).child('username').set(message.author.name)
    # Update the welcome cache to make sure the welcome messages cannot be exploited, with spam.
    firebase_db_obj.child('welcome_cache').child(str(message.author.id)).child(str(og_msg.id)).child(welcome_type).set(True)
    
    # Sallie reacts to the message with a sallie pink heart to confirm it's addition
    emoji_str_raw = '<:sallie_pink_shiny_heart:1305443467073163265>'
    emoji_str = re.findall(r'(?:<a?:\w+:\d+>|:\w+:)', emoji_str_raw)
    if emoji_str != [] :
        emoji = discord.PartialEmoji.from_str(emoji_str[0].strip())
    else :
        emoji = emoji_str_raw.strip()
    await message.add_reaction(emoji)
    return

def calculate_activity_index(lookback_duration: dt.timedelta) -> int :
    # If messages cache is empty then return.
    global activity_index_cache
    
    if len(activity_index_cache) == 0: return 0.0
    messages_cache_objs = [get_datetime_obj(ds) for old_ac_in, ds in activity_index_cache]

    now_time = datetime.now(dt.UTC)
    relevant_objs = [obj for obj in messages_cache_objs if (now_time - lookback_duration) <= obj <= now_time]

    time = lookback_duration.total_seconds() / 30 # 30 seconds as the minimum unit of time measurement.
    activity_index = (len(relevant_objs) / time) # Number of messages per unit time.
    return activity_index

def generate_activity_graph(lookback_duration: dt.timedelta, mode: str, grid = False) :
    # Mode can be h/m/s aka hours/minutes/seconds
    if mode not in 'hms': return None # If invalid mode provided return No graph.
    mode_index = 'hms'.index(mode) # Get a mode_index instead of a string, better for usage in indexing stuff.
    
    if len(activity_index_cache) == 0: return None # If no cache has been stored yet, return None.
    pass

    x_vals, y_vals = [], []
    for activity_indices, datetime_str in activity_index_cache :
        datetime_obj = get_datetime_obj(datetime_str)
        if not ((datetime.now(dt.UTC) - lookback_duration).replace(tzinfo = dt.UTC) < datetime_obj < datetime.now(dt.UTC)): break
        x_vals.append(datetime_obj.strftime('%H:%M'))
        y_vals.append(activity_indices[mode_index])
        continue
    
    # Plotting
    plt.figure(figsize = (14, 10))
    plt.plot(x_vals, y_vals, marker = '.', linestyle = '-', color = 'orange')
    
    tick_ratio = max(1, math.floor(len(x_vals) / DESIRED_TICK_NUM))
    selected_ticks = x_vals[ : : tick_ratio]  # Select every <tick-ratio>th point
    plt.xticks(selected_ticks, [ds for ds in selected_ticks])
    
    # Label the x-axis and y-axis
    plt.xlabel("Time")
    plt.ylabel('Activity Index')
    plt.title("Activity Chart")
    plt.grid(grid)
    plt.tight_layout()  # Adjust layout for better fit

    # Save the plot to an in-memory buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)  # Reset buffer position
    plt.close()  # Close the plot to free memory
    return buffer

@bot.event
async def on_message(message) :
    global voice_client, HELP_DICT, SLAPPING_SALAMANDER_SERVER_ACCENT, BOOSTER_NOTIF_CHANNEL_ID, LEVELUP_TIMES, activity_index_cache, CACHE_RETENTION_DURATION, activity_index_db_upload_time, ACTIVITY_INDEX_DB_CACHING_DURATION, current_bot_status, BOT_STATUSES, status_rotation_time, STATUS_ROTATION_DURATION
    
    print(f'[MESSAGE LOG]: {message.author} | {message.content}')
    if message.interaction_metadata != None :
        print(f'INTERACTION DETECTED SEXY BOI {message.content} | {message.interaction_metadata.interacted_message} | {message.interaction_metadata.user.name} | {message.interaction.name}')
        
        if message.interaction.name == 'bump' :
            await message.channel.send(f'HEY THANKS {message.interaction_metadata.user.mention} FOR BUMPING MAN, I DETECTED IT CUZ YOU ARE SO SEXY!!!')
            
            name = firebase_db_obj.child('bump').child(message.interaction_metadata.user.id).child('username').get().val()
            count = firebase_db_obj.child('bump').child(message.interaction_metadata.user.id).child('count').get().val() or 0
            
            print(name, count)
            
            firebase_db_obj.child('bump').child(str(message.interaction_metadata.user.id)).child('username').set(message.interaction_metadata.user.name)
            firebase_db_obj.child('bump').child(str(message.interaction_metadata.user.id)).child('count').set(count + 1)
        elif message.interaction.name == 'confess' :
            print('THE PERSON WHO TRIED CONFESSING WAS: %s', message.interaction_metadata.user.name)
        return
    
    if message.type == discord.MessageType.premium_guild_subscription :
        # Its a boost notif.
        booster = message.author
        
        await on_boost(booster)
        return
    elif message.channel.type == discord.ChannelType.private :
        ## Can be added in later if needed, removed cuz I feel like its required for us to also see sallie's messages for continuity of message flow in DMs
        # if message.author.id != BOT_SELF_USER_ID :
        dm_log_channel = bot.get_channel(SALLIE_DM_LOG_CHANNEL_ID) # Fetches the DM Logging Channel for sallie. Uses non async way to prevent ratelimit issues.

        # The section under this essentially divides a too long message sent by a nitro user or otherwise, into smaller manageable parts to send off separately.
        DM_LOG_CHAR_LIM = 1000 # Half of 2000[discord's max message length for free users] to get some leeway if needed.
        parts = []
        start, end = 0, 0
        while end < len(message.content) :
            if (end - start) >= DM_LOG_CHAR_LIM :
                parts.append(message.content[start : end])
                start = end
            end += 1
            continue
        if (end - start) != 0: parts.append(message.content[start : end])

        # Prepares and sends the messages in parts if needed, with the appropriate info annotated above it.
        msg_creation_time_str = message.created_at.strftime(datetime_date_format)
        initial_log_annotation = f'* __**Author:**__ ```{message.author.name} ({message.author.display_name})``` {message.author.mention}\n* __**Message-ID:**__ ```{message.id}```\n* __**Created-At:**__ ```{msg_creation_time_str}```\n'
        for p, part in enumerate(parts) :
            part_annotation = f'* __**Part:**__ {p + 1}\n'
            part_content = f'{initial_log_annotation}{part_annotation}> {part}'
            await dm_log_channel.send(part_content)
            continue
        
    elif message.type == discord.MessageType.reply :
        # ... check for qotd count[TODO] and welcome count[currently in development]
        await welcome_count_check(message)
    
    # await run_defamer_check()
    if message.channel.type != discord.ChannelType.private and message.author.id != BOT_SELF_USER_ID and (not message.author.bot) :
        if message.guild.id == PET_OWNER_GUILD :
            activity_index_cache_entry = [[calculate_activity_index(dt.timedelta(hours = 1)), calculate_activity_index(dt.timedelta(minutes = 1)), calculate_activity_index(dt.timedelta(seconds = 10))], get_datetime_str(message.created_at)]
            activity_index_cache.append(activity_index_cache_entry)
    activity_index_cache = [cache_entry for cache_entry in activity_index_cache if datetime.now(dt.UTC) >= get_datetime_obj(cache_entry[1]) >= (datetime.now(dt.UTC) - dt.timedelta(days = CACHE_RETENTION_DURATION)).replace(tzinfo = dt.UTC)]

    # Updating the activity_index_cache value in db every hour.
    if message.created_at.replace(tzinfo = dt.UTC) > get_datetime_obj(activity_index_db_upload_time) :
        firebase_db_obj.child('activity_index_cache').set(activity_index_cache)
        activity_index_db_upload_time = get_datetime_str(get_datetime_obj(activity_index_db_upload_time) + dt.timedelta(hours = ACTIVITY_INDEX_DB_CACHING_DURATION))

    # Rotating the bot status every 10 minutes.
    if message.created_at.replace(tzinfo = dt.UTC) > get_datetime_obj(status_rotation_time) :
        current_bot_status = random.choice([status for status in BOT_STATUSES if status != current_bot_status])
        bot_activity = discord.Game(name = current_bot_status, start = bot.user.created_at)
        await bot.change_presence(activity = bot_activity)
        status_rotation_time = get_datetime_str(get_datetime_obj(status_rotation_time) + dt.timedelta(minutes = STATUS_ROTATION_DURATION))
        
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
        
        name = firebase_db_obj.child('slap').child(message.author.id).child('username').get().val()
        count = firebase_db_obj.child('slap').child(message.author.id).child('count').get().val() or 0
        
        print(name, count)
        count += get_boost_gain(1, message.author)
        
        firebase_db_obj.child('slap').child(str(message.author.id)).child('username').set(message.author.name)
        firebase_db_obj.child('slap').child(str(message.author.id)).child('count').set(count)
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
    if message.content.lower().startswith('$$lb ') :
        lb_type = message.content.lower()[len('$$lb ') : ]
        lb_data = fetch_counter_data(lb_type)

        verb = {'slap': 'slapping', 'bump': 'bumping', 'welcome': 'welcoming', 'level': 'levels/xp'}
        embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT), title = f'{lb_type.title()} Leaderboards',
                              description = f'Given below is the top 25 leaderboard for {verb[lb_type]}:')
        
        rank = 1
        for member_name in sorted(lb_data, key = lb_data.get, reverse = True)[:25] :
            name = f'{rank}. {member_name}'
            desc = f'{lb_data[member_name]} points'
            embed.add_field(name = name, value = desc, inline = False)
            rank += 1
            continue
        await message.channel.send(embed = embed)
    if message.content.lower().startswith('$$revive') :
        list_of_revivals = []
        for mention in message.mentions :
            if mention == message.author : continue
            if mention.dm_channel == None :
                await mention.create_dm()
            try :
                await mention.dm_channel.send('Hii!! Sallie this side ^^! You stopped slapping me :<! Me and the others really miss you :3 will you take some time to visit our server again? It\'d make us all soo happy :D!! ' + message.channel.mention)
                list_of_revivals.append(mention.name)
            except :
                pass
            continue
        if list_of_revivals :
            await message.channel.send('Revival message sent to {revivals}!'.format(revivals = ', '.join(list_of_revivals)))
        else :
            await message.channel.send('You cannot revive yourself silly! You are already alive!! Grrrr')
    if message.content.lower() == '$$my_discord_id' :
        await message.channel.send(f'Your discord ID is: ```{message.author.id}```')
    if message.author.id == BOT_OWNER_ID and message.content.lower().startswith('$$boost ') :
        booster = message.mentions[0]
        
        await on_boost(booster)
        await message.channel.send('Noted master adi! I have modified my databases as per ur wishes hehe!!')
        return
    if message.content.lower().startswith('$$rank') or message.content.lower().startswith('$$level') :
        await generate_rank_card(message)
    if message.content.lower().startswith('$$echo ') and message.author.id == BOT_OWNER_ID :
        try :
            content = ' '.join(message.content.split(' ')[2 : ])
            if (content.replace(' ', '') == '') and message.type == discord.MessageType.reply :
                parent_msg = message.reference.cached_message or (await message.channel.fetch_message(message.reference.message_id))
                content = parent_msg.content
            channel = message.channel_mentions[0]
            await channel.send(f'{content}')
            await message.channel.send('Echoed successfully!')
        except :
            await message.channel.send('Something went wrong when trying to execute this command :<')
    if message.content.lower().startswith('$$echo_dm') and message.author.id == BOT_OWNER_ID :
        try :
            content = ' '.join(message.content.split(' ')[2 : ])
            if (content.replace(' ', '') == '') and message.type == discord.MessageType.reply :
                parent_msg = message.reference.cached_message or (await message.channel.fetch_message(message.reference.message_id))
                content = parent_msg.content
            mention = message.mentions[0]
            if mention != message.author : 
                if mention.dm_channel == None :
                    await mention.create_dm()
                try :
                    await mention.dm_channel.send(f'{content}')
                    await message.channel.send(f'DM Sent to {mention.mention} successfully!')
                except :
                    await message.channel.send(f'DM could not be sent to {mention.mention} :disappointed: . They have me blocked! Please punish them for this adi master >w<~!')
            else :
                await message.channel.send('Why you tryna dm your own self cutie patootie~?')
        except :
            await message.channel.send('Something went wrong when trying to execute this command :<')
    if message.content.lower().startswith('$$echo_reply') and message.author.id == BOT_OWNER_ID :
        # $$echo_reply <channel_mention> <message_id> <content>
        try :
            cmd_args = message.content.split(' ')
            content = ' '.join(cmd_args[3 : ])
            if (content.replace(' ', '') == '') and message.type == discord.MessageType.reply :
                parent_msg = message.reference.cached_message or (await message.channel.fetch_message(message.reference.message_id))
                content = parent_msg.content
            channel = message.channel_mentions[0]
            message_id = int(cmd_args[2])
            
            try :
                msg = channel.get_partial_message(message_id)
                await msg.reply(f'{content}')
            except :
                msg = await channel.fetch_message(message_id)
                await msg.reply(f'{content}')

            await message.channel.send('Reply sent successfully!')
        except :
            await message.channel.send('Something went wrong when trying to execute this command :<')
    if message.content.lower().startswith('$$echo_dm_reply') and message.author.id == BOT_OWNER_ID :
        # $$echo_dm_reply <mention> <message_id> <content>
        try :
            cmd_args = message.content.split(' ')
            content = ' '.join(cmd_args[3 : ])
            if (content.replace(' ', '') == '') and message.type == discord.MessageType.reply :
                parent_msg = message.reference.cached_message or (await message.channel.fetch_message(message.reference.message_id))
                content = parent_msg.content
            mention = message.mentions[0]
            channel = mention.dm_channel
            message_id = int(cmd_args[2])
            
            try :
                msg = channel.get_partial_message(message_id)
                await msg.reply(f'{content}')
            except :
                msg = await channel.fetch_message(message_id)
                await msg.reply(f'{content}')

            await message.channel.send('Reply sent successfully!')
        except :
            await message.channel.send('Something went wrong when trying to execute this command :<')
    if message.content.lower().startswith('$$echo_react') and message.author.id == BOT_OWNER_ID :
        # $$echo_react <channel_mention> <message_id> <reaction>
        try :
            cmd_args = message.content.split(' ')
            channel = message.channel_mentions[0]
            message_id = int(cmd_args[2])
            emoji_str_raw = ' '.join(cmd_args[3 : ])
            emoji_str = re.findall(r'(?:<a?:\w+:\d+>|:\w+:)', emoji_str_raw)
            
            if emoji_str != [] :
                emoji = discord.PartialEmoji.from_str(emoji_str.strip())
            else :
                emoji = emoji_str_raw.strip()
            
            try :
                msg = channel.get_partial_message(message_id)
                await msg.add_reaction(emoji)
            except :
                msg = await channel.fetch_message(message_id)
                await msg.add_reaction(emoji)

            await message.channel.send('Reacted to the message successfully!')
        except Exception as e :
            print(e)
            
            await message.channel.send('Something went wrong when trying to execute this command :<')
    if message.content.lower() in ['$$server_website', '$$website'] :
        await message.channel.send('Here ya go! Lemme link you up with the server\'s website really quickly :3! https://sallie-bot.onrender.com/home ')
    if message.content.lower().startswith('$$activity_index ') :
        try :
            duration = message.content.lower()[len('$$activity_index ') : ]
            duration_parts = duration.strip().split(' ')

            if duration_parts == [] :
                await message.channel.send('Proper lookback duration has not been provided for calculation of activity index.')
            else :
                hour_instances = [h for h in duration_parts if h.endswith('h')]
                min_instances = [m for m in duration_parts if m.endswith('m')]
                sec_instances = [s for s in duration_parts if s.endswith('s')]
    
                hours = int(hour_instances[0][ : -1]) if hour_instances else 0.0
                minutes = int(min_instances[0][ : -1]) if min_instances else 0.0
                seconds = int(sec_instances[0][ : -1]) if sec_instances else 0.0
    
                # if hours == minutes == seconds == 0.0 :
                #     await message.channel.send('Proper lookback duration has not been provided for calculation of activity index.')
                # else :
                activity_index = calculate_activity_index(dt.timedelta(hours = hours, minutes = minutes, seconds = seconds))
                await message.channel.send(f'YESH! BEEP BOOP... 🤖🦎 *robotic lizard noises*, calculating.. activity.. index... boop. beep.\n* Activity Index: \n```{activity_index}```\n')
        except ValueError as e:
            print(e)
            await message.channel.send('Command syntax was not followed and the lookback duration arguments were not integers. Try again.')
    if message.content.lower().startswith('$$activity_graph ') or message.content.lower().startswith('$$activity_chart ') :
        args = message.content.lower()[len('$$activity_graph ') : ].strip().split(' ')
        if len(args) < 2 :
            await message.channel.send('Arguments not passed properly to the command, to generate an activity chart, I need the chart mode and lookback duration!! <33 Please try again~')
        else :
            mode = args[0]
            mode_aliases = {'h': ['hr', 'hrs', 'hour', 'hours'], 'm': ['min', 'mins', 'minute', 'minutes'], 's': ['sec', 'secs', 'second', 'seconds']}
            for mode_main in mode_aliases :
                if mode in mode_aliases[mode_main] :
                    mode = mode_main
                    break
                continue
            if mode not in 'hms':
                await message.channel.send('ERMM... WHAT THE SIGMA~ You passed an invalid mode type sweetheart 😊✨!')
            else :
                grid_bool = ([arg == '-g' for arg in args[1 : ] if arg == '-g'] or [False])[0]
                duration_parts = args[1 : ]
                if duration_parts == [] :
                    await message.channel.send('Proper lookback duration has not been provided for plotting of the activity chart.')
                else :
                    hour_instances = [h for h in duration_parts if h.endswith('h')]
                    min_instances = [m for m in duration_parts if m.endswith('m')]
                    sec_instances = [s for s in duration_parts if s.endswith('s')]
        
                    hours = int(hour_instances[0][ : -1]) if hour_instances else 0.0
                    minutes = int(min_instances[0][ : -1]) if min_instances else 0.0
                    seconds = int(sec_instances[0][ : -1]) if sec_instances else 0.0

                    lookback_duration = dt.timedelta(hours = hours, minutes = minutes, seconds = seconds)
                    activity_chart_buffer = generate_activity_graph(lookback_duration, mode, grid_bool)

                    # Create a Discord file from the buffer
                    chart_file = discord.File(activity_chart_buffer, filename = 'graph.png')
                
                    # Create an embed with the graph
                    embed = discord.Embed(color = discord.Colour.from_str(SLAPPING_SALAMANDER_SERVER_ACCENT),
                                          title = 'Activity Chart',
                                          description = 'Given below is the activity chart generated for the provided specifications')
                    embed.set_image(url = "attachment://graph.png")
                
                    # Send the embed with the attached graph
                    await message.channel.send(file = chart_file, embed = embed)
                    pass
    if message.content.lower().startswith('$$debug_get ') :
        arg = message.content[len('$$debug_get ') : ]
        if arg not in globals() :
            await message.channel.send('Invalid variable queried, not available in globals.')
        else :
            debug_val_content = f'{globals()[arg]}'
            parts = []
            start, end = 0, 0
            while end < len(debug_val_content) :
                if (end - start) >= 1900 :
                    parts.append(debug_val_content[start : end])
                    start = end
                end += 1
                continue
            if (end - start) != 0: parts.append(debug_val_content[start : end])

            for part in parts :
                await message.channel.send(f'```py\n{part}```')
                continue
    if message.content.lower().startswith('$$debug_set ') :
        try :
            arg = message.content[len('$$debug_set ') : ]
            args = arg.split('=')
            var_name = args[0].strip()
            var_value = '='.join(args[1 : ])
            globals()[var_name] = var_value
            await message.channel.send(f'Global variable with the name {var_name} has been set to the value provided.')
        except Exception as e :
            print(e)
            await message.channel.send('Something went wrong, could not set the variable globally. Try again or give up baby boy~')
    
    
    if (not message.author.bot) and (not message.channel.id == SPAM_CHANNEL_ID) :
        if message.author.id in LEVELUP_TIMES :
            if not ((datetime.now(dt.UTC) - LEVELUP_TIMES[message.author.id]['time']) > dt.timedelta(seconds = 60)) :
                return
            if LEVELUP_TIMES[message.author.id]['content'] == message.content :
                return
        
        level_msg_template = 'YAYY!!! {mention} just reached a new level of slapping, by slapping a total of {level} thousand salamanders!'
        
        name = firebase_db_obj.child('levels').child(message.author.id).child('username').get().val()
        xp = firebase_db_obj.child('levels').child(message.author.id).child('xp').get().val() or 0
        level = firebase_db_obj.child('levels').child(message.author.id).child('level').get().val() or 0
        
        xp += get_boost_gain(random.uniform(15, 25), message.author, float_allowed = True)
        new_level = calculate_level(xp, level_func)
        if ((new_level - level) > 0) :
            await message.channel.send(level_msg_template.format(mention = message.author.mention, level = new_level))
        
        firebase_db_obj.child('levels').child(str(message.author.id)).child('username').set(message.author.name)
        firebase_db_obj.child('levels').child(str(message.author.id)).child('xp').set(xp)
        firebase_db_obj.child('levels').child(str(message.author.id)).child('level').set(new_level)
        
        LEVELUP_TIMES[message.author.id] = {'time': datetime.now(dt.UTC), 'content': message.content}
    return

async def BOT_MAIN_FUNC(BOT_TOKEN) :
    bot.run(BOT_TOKEN)
    return

if __name__ == '__main__' :
    BOT_TOKEN = os.environ['BOT_TOKEN']
    asyncio.run(BOT_MAIN_FUNC(BOT_TOKEN))
