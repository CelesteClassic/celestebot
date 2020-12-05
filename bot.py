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

class CelesteBot(commands.Bot):

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(command_prefix='!', intents=intents)
        self.logger = logging.getLogger('discord')

        with open('custom_commands.json', 'r') as f:
            self.custom_commands = json.load(f)

        for extension in extensions:
            self.load_extension(extension)
            
    async def on_member_join(self, member):
        await member.guild.get_channel(495648733057253391).send("Welcome! <:yadelie:642375995961114636>")

    async def on_ready(self):
        self.uptime = datetime.datetime.utcnow()

        game = discord.Game("gemskip 2400m")
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
