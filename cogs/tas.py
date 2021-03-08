from discord.ext import commands
import discord
import asyncio
import subprocess
import requests
from datetime import datetime
from datetime import timedelta

from discord_slash import SlashCommand
from discord_slash import SlashContext

import git
import json
from distutils.dir_util import copy_tree
import zipfile
import os
import shutil
from pathlib import Path
import traceback


# shoutouts to gonen
def updateAndCommit(data, game, category):
    home = str(Path.home())
    gitPath=home+'/tasdatabase'
    repo = git.Repo(gitPath)
    #repo.git.fetch('--all')
    #repo.git.reset('--hard', 'origin/master')

    inputs=list(map(int,data[data.index("]")+1:].split(',')[:-1]))
    framecount=len(inputs)-1
    dashnum=0
    for i in inputs:
        if i&32:
            dashnum+=1

    jsonPath=os.path.join(gitPath,'database.json')
    with open(jsonPath,'r') as f:
        data=json.load(f)

    change=None
    for lvl in data[game][category]:
        if lvl['file']==fileName:
            change=lvl
    if change is None:
        print(f"no file in {game}/{category} with filename {fileName}")
        return

    oldframes=change['frames']
    if oldframes==None:
        return
    change['frames']=framecount
    if 'dashes' in category:
        change['dashes']=dashnum

    with open(jsonPath, 'w') as f:
        json.dump(data,f,indent=4)

    rootPath = os.path.join(gitPath, game, category)


    zipPath=os.path.join(rootPath,f"Full{game.capitalize()}{category.capitalize()}.zip")
    with zipfile.ZipFile(zipPath,"w") as zf:
        for file in os.listdir(rootPath):
            if file.endswith(".tas"):
                zf.write(os.path.join(rootPath,file),os.path.join("TAS",file))

    repo.index.add([os.path.join(rootPath,fileName),jsonPath,zipPath])
    commit_msg=f'updated {game} {category} {change["name"]} to be {framecount}f ({framecount-oldframes:+}f) (automated)'
    repo.index.commit(commit_msg)
    repo.remotes.origin.push()

def run():
    process = subprocess.Popen("love ~/UniversalClassicTas/CelesteTAS/ &", stdout=subprocess.PIPE, shell=True)
    final_time = None
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            if output.strip() == b'maybe it ended idk':
                return final_time
            elif output.strip() == b'death':
                return None
            else:
                final_time = output.strip()


class Tas(commands.Cog):

    async def is_mod(ctx):
        return ctx.author.guild_permissions.manage_channels

    def __init__(self, bot):
        self.bot = bot

        #self.base_url = "https://celesteclassic.github.io/tasdatabase/{}/{}/"

        self.base_categories = {('100', 'any', 'gemskipany', 'key'): 'any', ('nodiag'): 'nodiag', ('mindashes'): 'mindashes'}
        self.games = {('classic', 'vanilla', 'main'): 'classic', ('terra', 'australis'): 'australis', ('adelie',): 'adelie',
                      ('everred', 'ever red'): 'everred', ('impossibleste', 'impossible celeste'): 'impossibleste', ('noeleste',): 'noeleste',
                      ('old site', 'oldsite'): 'oldsite', ('perisher',): 'perisher'}
        self.categories = {('hundo', '100%', '100'): '100', ('any', 'any%'): 'any', 
                    ('minimum dashes', 'min dashes', 'mindashes'): 'mindashes', ('gemskip', 'gem-skip', 'gem skip'): 'gemskip',
                    ('key', 'key%'): 'key', ('nodiag', 'no diagonal dashes', 'no diag'): 'nodiag'}

        self.slash = SlashCommand(bot, override_type=True)
    
        @self.slash.slash(name="categories")
        async def categories(ctx):
            await ctx.send(3, content=f"Possible games in the TAS database: {list(self.games.values())}\n\nPossible categories in the TAS database: {list(self.categories.values())}", hidden=True)


        @self.slash.slash(name="tas")
        async def tas(ctx, game, category, levelname, hidden=False):
            r = requests.get(f"https://celesteclassic.github.io/tasdatabase/database.json")

            
            if levelname.isdigit() and not levelname.startswith("m"):
                levelname+="m"
            try:
                j = r.json()[game][category]
            except KeyError:
                await ctx.send(content="Invalid game or category!", hidden=hidden)
                return

            for level in j:

                if level["name"].lower() == levelname.lower():
                
                    frames = level["frames"]
                    name = level["name"]
                    filename = level["file"]

                    embed = discord.Embed(color=0xFF004D)
                    embed.set_footer(text="Collected from the TAS Database")
                    embed.description = f"{game.capitalize()} {category} {name} is {frames}f"

                    if filename:
                        embed.description += f"\n[TAS File](https://celesteclassic.github.io/tasdatabase/{game}/{category}/{filename})"
                    if hidden:
                        await ctx.send(3, content=embed.description, hidden=True)
                    else:
                        await ctx.send(embeds=[embed])
                    break

    """ Old commands, should remove after discord.py gets support for slash commands"""
    @commands.command()
    async def categories(self, ctx):
        await ctx.send(f"Possible games in the TAS database: {list(self.games.values())}\n\nPossible categories in the TAS database: {list(self.categories.values())}")

    @commands.check(is_mod)
    @commands.command(aliases=["updatetas", "sendtas"])
    async def uploadtas(self, ctx, game, category):
        if len(ctx.message.attachments) > 0:
            try:
                data = (await ctx.message.attachments[0].read()).decode("utf-8")
                updateAndCommit(data, game, category)
                await ctx.send("TAS File uploaded (probably)!")
            except:
                traceback.print_exc()
                await ctx.send("Something went wrong while uploading the TAS file! (tell cominixo)")
        else:
            await ctx.send("Please include an attachment with the message")

    @commands.command()
    async def tas(self, ctx, game, category, *, levelname):
        r = requests.get(f"https://celesteclassic.github.io/tasdatabase/database.json")

        
        if levelname.isdigit() and not levelname.startswith("m"):
            levelname+="m"
        try:
            j = r.json()[game][category]
        except KeyError:
            await ctx.send("Invalid game or category!")
            return
        print([i for i in j])

        for level in j:

            if level["name"].lower() == levelname.lower():
            
                frames = level["frames"]
                name = level["name"]
                filename = level["file"]

                embed = discord.Embed(color=0xFF004D)
                embed.set_footer(text="Collected from the TAS Database")
                embed.description = f"{game.capitalize()} {category} {name} is {frames}f"

                if filename:
                    embed.description += f"\n[TAS File](https://celesteclassic.github.io/tasdatabase/{game}/{category}/{filename})"

                await ctx.send(embed=embed)
                break

def setup(bot):
    bot.add_cog(Tas(bot))
