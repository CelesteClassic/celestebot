from discord.ext import commands
import discord

import json

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def is_mod(ctx):
        return ctx.author.guild_permissions.manage_channels

    @commands.command(aliases=['addcommand', 'newcommand'])
    @commands.check(is_mod)
    async def setcommand(self, ctx, command, *, message):
        self.bot.custom_commands["!" + command] = message
        with open('custom_commands.json', 'w') as f:
            json.dump(self.bot.custom_commands, f)

        await ctx.send(f"Set message for command {command}")

    @commands.command(aliases=['deletecommand'])
    @commands.check(is_mod)
    async def removecommand(self, ctx, command):
        del self.bot.custom_commands["!" + command]
        with open('custom_commands.json', 'w') as f:
            json.dump(self.bot.custom_commands, f)

        await ctx.send(f"Removed command {command}")

def setup(bot):
    bot.add_cog(Admin(bot))