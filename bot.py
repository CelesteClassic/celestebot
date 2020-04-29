from discord.ext import commands
import discord
import logging

import datetime
import config
import json

import asyncio
import subprocess
from multiprocessing import Pool

extensions = [
    "cogs.utils",
    "cogs.src",
    "cogs.tas",
    "cogs.admin"
]


def run():
    process = subprocess.Popen("Xvfb :99 & DISPLAY=:99 love ~/UniversalClassicTas/CelesteTAS/ &", stdout=subprocess.PIPE, shell=True)
    final_time = None
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            if output.strip() == b'maybe it ended idk':
                return final_time
            else:
                final_time = output.strip()

class CelesteBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='!')
        self.logger = logging.getLogger('discord')

        with open('custom_commands.json', 'r') as f:
            self.custom_commands = json.load(f)

        for extension in extensions:
            self.load_extension(extension)
            
    

    async def on_ready(self):
        self.uptime = datetime.datetime.utcnow()

        game = discord.Game("gemskip 2300m")
        await self.change_presence(activity=game)

        self.logger.warning(f'Online: {self.user} (ID: {self.user.id})')

    async def on_message(self, message):

        if message.author.bot:
            return

        if message.content:
            command = message.content.split()[0] 

            if command in self.custom_commands:
                
                await message.channel.send(self.custom_commands[command])
                return
        
        

        await self.process_commands(message)

    def run(self):
        super().run(config.token, reconnect=True)
