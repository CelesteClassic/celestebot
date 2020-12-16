from discord.ext import commands
from discord.ext import tasks
from discord_slash import SlashCommand
from discord_slash import SlashContext
import discord
import requests
import config
import asyncio

class Utils(commands.Cog):

    async def convert(self, ctx, argument):

        argument_list = argument.split()
        if not argument:
            return None
        # return a list with query + page if last number is a page
        try:
            page = int(argument_list[-1])
            if 0 < page < 100:
                return [" ".join(argument_list[0:-1]), page]

            else:
                return argument
        except ValueError:
            return argument
    
    def __init__(self, bot):
        self.bot = bot
        self.database_url = "https://celesteclassic.github.io/gifs/"

        self.slash = SlashCommand(bot, override_type=True)

        @self.slash.slash(name="ping")
        async def _ping(ctx: SlashContext):
            #"""Shows the Client Latency."""
            await ctx.send(3, content=f'Pong! {round(self.bot.latency*1000)}ms', hidden=True)
            

        @self.slash.slash(name="database")
        async def database(ctx, category=None, level=None, page=None, hidden=False):
            
            print(category, level, page, hidden)

            # dumb workaround

            if isinstance(level, bool):
                hidden = level
                level = ""
            elif isinstance(page, bool):
                hidden = page
                page = ""

            if str(category).isdigit():
                if isinstance(level, int):
                    page = level
                if category < 100:
                    page = category
                    level = ""
                else:
                    level = category
                category = ""

            
            
            if level:
                if not page and level < 100:
                    page = level
                    level = ""
            
            if level:
                query = str(level) + " " + category

            else:
                query = category

            if (page):
                index = page-1
            else:
                index = 0

            # end of dumb workaround

            print(category, level, page, hidden)


            query = query.split()

            gifs = requests.get(self.database_url + "database.json").json()

            result = []

            for gif in gifs:
                if all(tag in gif['tags'] for tag in query):
                    result.append(self.database_url + gif['url'])

            total_pages = len(result)

            if total_pages == 0:
                await ctx.send(3, content="No results for the query.", hidden=hidden)
                return

            index = index%total_pages
            
            embed = discord.Embed(color=0xFF004D)
            embed.set_image(url=result[index])
            embed.set_footer(text=f"Page {index+1}/{total_pages}")

            if hidden:
                await ctx.send(3, content=result[index], hidden=hidden)
                return

            # Manually doing the request to just ack (type 5)

            base = {
                "type": 5
            }
            
            await ctx._http.post(base, ctx._discord.user.id, ctx.interaction_id, ctx._SlashContext__token, True)

            message = await ctx.channel.send(embed=embed)
            await message.add_reaction("⬅")
            await message.add_reaction("➡")
            
            def check(reaction, user):
                return user == ctx.author and str(reaction.emoji) in ["➡", "⬅"]

            
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                except asyncio.TimeoutError:
                    break
                else:
                    await message.remove_reaction(reaction.emoji, user)
                    if reaction.emoji == "➡":
                        index += 1
                    else:
                        index -= 1

                    index = index%total_pages


                    embed.set_image(url=result[index])
                    embed.set_footer(text=f"Page {index+1}/{total_pages}")
                    await message.edit(embed=embed)

    

def setup(bot):
    bot.add_cog(Utils(bot))
