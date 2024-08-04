# -*- coding: utf-8 -*-
"""
Created on Thu May 23 02:31:45 2024

@author: ketch
"""

import bot
import os
import discord
import asyncio

while __name__ == '__main__':
    try :
        bot.keep_alive()
        asyncio.run(bot.BOT_MAIN_FUNC(os.environ['BOT_TOKEN']))
        bot.run()
    except discord.errors.HTTPException as e:
        print(e)
        print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")