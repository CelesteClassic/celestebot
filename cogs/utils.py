from discord.ext import commands
from discord.ext import tasks
import discord
import requests
import config
import asyncio

class Utils(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.database_url = "https://celesteclassic.github.io/gifs/"

    class QueryConverter(commands.Converter):
        async def convert(self, ctx, argument):

            argument_list = argument.split()
            # return a list with query + page if last number is a page
            try:
                page = int(argument_list[-1])
                if 0 < page < 100:
                    return [" ".join(argument_list[0:-1]), page]

                else:
                    return argument
            except ValueError:
                return argument

    @commands.command(aliases=["db", "gif", "gifdb", "gifs"])
    async def database(self, ctx, *, query: QueryConverter):

        # if last element is an int then it's a page
        if (isinstance(query[-1], int)):
            index = query[-1] - 1
            query = query[0]
        else:
            index = 0

        query = query.split()

        gifs = requests.get(self.database_url + "database.json").json()

        result = []

        for gif in gifs:
            if all(tag in gif['tags'] for tag in query):
                result.append(self.database_url + gif['url'])

        total_pages = len(result)

        index = index%total_pages
        print(index)
        
        embed = discord.Embed(color=0xFF004D)
        embed.set_image(url=result[index])
        embed.set_footer(text=f"Page {index+1}/{total_pages}")

        message = await ctx.send(embed=embed)
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
