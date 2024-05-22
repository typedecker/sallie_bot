# -*- coding: utf-8 -*-
"""
Created on Thu May 23 02:31:45 2024

@author: ketch
"""

import bot
import os
import discord

while __name__ == '__main__':
    try :
        bot.keep_alive()
        bot.bot.run(os.environ['BOT_TOKEN'])
        bot.run()
    except discord.errors.HTTPException as e:
        print(e)
        print("\n\n\nBLOCKED BY RATE LIMITS\nRESTARTING NOW\n\n\n")
        os.system('kill 1')