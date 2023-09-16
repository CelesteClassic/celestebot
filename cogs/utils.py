from discord.ext import commands
from discord.ext import tasks
import discord
import requests
import config
import asyncio
import random

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
        await interaction.response.defer()
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
    async def disclaimer(self, ctx):
        # Send the text of a random defined command that starts with
        # "disclaimer"; this allows defining new disclaimers with addcommand,
        # and also sending any particular one if you know its true name.
        #await ctx.send(random.choice([val for key,val in self.bot.custom_commands.items() if key.startswith("!disclaimer")] or ["DISCLAIMER: No disclaimers defined"]))
        #
        # Alternatively, just hardcode.
        # This is formatted as a dict instead of a list for easier insertion
        # into a certain json file
        await ctx.send(random.choice(list({
            "!disclaimer_old":     "this is getting old <:zzzdelie:709561310186045540>",
            "!disclaimer_dciydk":  "DISCLAIMER: Don't click if you don't know",
            "!disclaimer_3":       "DISCLAIMER: This disclaimer message will self-destruct",
            "!disclaimer_4":       "DISCLAIMER: If you can read this you're in range",
            "!disclaimer_5":       "DISCLAIMER: Highly flammable",
            "!disclaimer_6":       "DISCLAIMER: Chocking hazard",
            "!disclaimer_warn":    "WARNING: Improper usage of the word \"disclaimer\"",
            "!disclaimer_none":    "DISCLAIMER: None :)",
            "!disclaimer_9":       "DISCLAIMER: Disclaimer messages may be inaccurate",
            "!disclaimer_c":       "DISCLAIMER: No copyright infringement intended",
            "!disclaimer_nsfw":    "DISCLAIMER: Content not suitable for all audiences",
            "!disclaimer_clam":    "DISCLAM: Any bivalve molluscs will be removed",
            "!disclaimer_nuclear": "DISCLAIMER: This is not a place of honor",
            "!disclaimer_dante":   "DISCLAIMER: Abandon all hope, ye who enter here",
            "!disclaimer_memorial":"DISCLAIMER: This disclaimer to those who perished on the climb",
            "!disclaimer_tas":     "DISCLAIMER: Tell cominixo",
            "!disclaimer_17":      "DISCLAIMER: Help I'm trapped in a disclaimer factory",
            "!disclaimer_pr":      "DISCLAIMER: Has not been peer-reviewed",
            "!disclaimer_cite":    "DISCLAIMER: [citation needed]",
            "!disclaimer_paywall": "DISCLAIMER: You've used up all of your free disclaimers! Subscribe for just 2.99$/month to get unlimited access",
            "!disclaimer_21":      "DISCLAIMER: Figuring out which claims were disclaimed is left as an exercise for the reader",
            "!disclaimer_airfryer":"DISCLAIMER: The author of the following content does not own an air fryer",
            "!disclaimer_spike":   "DISCLAIMER: Spike did not kil",
            "!disclaimer_canon":   "DISCLAIMER: Not canon",
            "!disclaimer_florida": "DISCLAIMER: Banned in the state of Florida",
            "!disclaimer_endorse": "DISCLAIMER: Not endorsed by celestebot",
            "!disclaimer_":        "DISCLAIMER:",
            "!disclaimer_alan":    "DISCLAIMER: TODO: finish this disclaimer",
            "!disclaimer_notfunny":"DISCLAIMER: Not funny",
            "!disclaimer_30":      "DISCLAIMER: Traduzione non disponibile",
            }.values())))

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
    

async def setup(bot):
    await bot.add_cog(Utils(bot))
