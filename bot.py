from discord.ext import commands
import discord

import datetime
import config
import json

extensions = [
    "cogs.utils",
    "cogs.admin"
]

class CelesteBot(commands.Bot):

    def __init__(self):
        super().__init__(command_prefix='!')

        with open('custom_commands.json', 'r') as f:
            self.custom_commands = json.load(f)

        for extension in extensions:
            self.load_extension(extension)

    async def on_ready(self):
        self.uptime = datetime.datetime.utcnow()

        game = discord.Game("gemskip 2300m")
        await self.change_presence(activity=game)

        print(f'Online: {self.user} (ID: {self.user.id})')

    async def on_message(self, message):

        if message.author.bot:
            return

        command = message.content.split()[0] 

        if command in self.custom_commands:
            await message.channel.send(self.custom_commands[command])
            return

        await self.process_commands(message)

    def run(self):
        super().run(config.token, reconnect=True)
