from discord.ext import commands
from discord.ext import tasks
import discord
import requests
import config
import asyncio

class SwitchPageButton(discord.ui.Button['switchPage']):
    
    def __init__(self, position):
        super().__init__(style=discord.ButtonStyle.blurple, label='<' if position == 0 else '>')
        self.position = position


    async def callback(self, interaction: discord.Interaction):
        view: PageSwitcher = self.view
        view.currentpage = view.currentpage - 1 if self.position == 0 else view.currentpage + 1

        await view.update_page(interaction)

class PageSwitcher(discord.ui.View):

    def __init__(self, currentpage, totalpages, results):
        super().__init__()
        self.totalpages = totalpages
        self.currentpage = currentpage
        self.results = results
        self.add_item(SwitchPageButton(0))
        self.add_item(SwitchPageButton(1))
        self.update_buttons()
        
        
    async def update_page(self, interaction: discord.Interaction):

        self.currentpage %= self.totalpages
        self.update_buttons()

        embed = discord.Embed(color=0xFF004D)
        embed.set_image(url=self.results[self.currentpage])
        embed.set_footer(text=f"Page {self.currentpage+1}/{self.totalpages}")
        await interaction.message.edit(embed=embed, view=self)

    def update_buttons(self):
        if self.currentpage == 0:
            self.children[0].style = discord.ButtonStyle.grey
        else:
            self.children[0].style = discord.ButtonStyle.blurple
        
        if self.currentpage+1 == self.totalpages:
            self.children[1].style = discord.ButtonStyle.grey
        else:
            self.children[1].style = discord.ButtonStyle.blurple

class QueryConverter(commands.Converter):
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

    @commands.command()
    async def ping(self, ctx):
        #"""Shows the Client Latency."""
        await ctx.send(f'Pong! {round(self.bot.latency*1000)}ms')

    @commands.command()
    async def convert(self, ctx, numberstr):
        try:
            number = float(numberstr.replace("f", "").replace("s", ""))
        except:
            await ctx.send("Invalid number!")
        #"""Converts frames to seconds and seconds to frames"""
        if (int(number) != number) or "s" in numberstr:
            await ctx.send(f'{number} seconds is approximately {round(number*30)} frames')  
        else:
           await ctx.send(f'{int(number)} frames is {number/30:.3f} seconds')

    @commands.command(aliases=["db", "gif", "gifdb", "gifs"])
    async def database(self, ctx, *, query: QueryConverter = None):

        if not query:
            await ctx.send(self.database_url)
            return

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
        
        embed = discord.Embed(color=0xFF004D)
        embed.set_image(url=result[index])
        embed.set_footer(text=f"Page {index+1}/{total_pages}")

        message = await ctx.send(embed=embed, view=PageSwitcher(index, total_pages, result))
    

def setup(bot):
    bot.add_cog(Utils(bot))
