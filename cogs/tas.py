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


# shoutouts to gonen
def updateAndCommit(filePath, game, category):
    fileName=os.path.split(filePath)[1]
    home = str(Path.home())
    gitPath=home+'/tasdatabase'
    repo = git.Repo(gitPath)
    #repo.git.fetch('--all')
    #repo.git.reset('--hard', 'origin/master')

    with open(filePath, 'r') as f:
        data=f.read()
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

    @commands.Cog.listener()
    async def on_message(self, message):
        return
        if message.channel.id == 548203844992237578:
            if len(message.attachments) > 0:
                file = message.attachments[0]
		
                if file.filename.endswith(".tas"):

                    home = str(Path.home())

                    gitPath=home+'/tasdatabase'
                    repo = git.Repo(gitPath)
                    repo.git.stash()
                    repo.git.pull()

                    game_detected = 'classic'
                    category_detected = 'any'
                    secondary_category = None

                    if message.content:

                        # haha python
                        try:
     
                            game_detected = next(v for k, v in self.games.items() if any(game.lower() in message.content.lower() for game in k))

                        except StopIteration:
                            game_detected = 'classic'

                        it = (v for k, v in self.categories.items() if any(category.lower() in message.content.lower() for category in k))

                        for i in it:
                            if i == "gemskip":
                                category_detected = i
                                break
                            secondary_category = i
                        

                        if category_detected != "gemskip":
                            category_detected = secondary_category
                            secondary_category = None
                        elif secondary_category == None:
                            secondary_category = "any"
                    
                            
                    base_category = None

                    if category_detected != "gemskip":
                        for k, v in self.base_categories.items():
                            if category_detected in k:
                                base_category = v
                                break
                        
                    if secondary_category:
                        category_detected += secondary_category
                        base_category = secondary_category
                   
                    await message.channel.send(f'I see a TAS file! The detected category is {game_detected} {category_detected} with the base category {base_category}, please confirm this by sending a message with "yes" or "no", if you do not wish to upload this file, say "no" (or just do nothing)')
                    def check(m):
                        return ('no' in m.content.lower() or 'yes' in m.content.lower()) and m.channel == message.channel and m.author == message.author
                    
                    try:
                        msg = await self.bot.wait_for('message', check=check, timeout=30)
                    except TimeoutError:
                        await message.channel.send("Okay, this has been cancelled, for possible games and categories type !categories")
                        return
                    
                    if "no" in msg.content.lower():
                        await message.channel.send("Okay, this has been cancelled, for possible games and categories type !categories")
                        return

                    os.system(f"cp {home}/tasdatabase/{game_detected}/{base_category}/*.tas {home}/UniversalClassicTas/CelesteTAS/TAS")
                    try:
                        os.system(f"cp {home}/tasdatabase/{game_detected}/{category_detected}/*.tas {home}/UniversalClassicTas/CelesteTAS/TAS")
                    except:
                        await message.channel.send("This category doesn't exist for this game (yet?)")
                        return

                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, run)      
                    oldtime = datetime.strptime(result.decode("utf-8").split("(")[0][:-1][:10], "%M:%S.%f")

                    filePath = f"{home}/tasdatabase/{game_detected}/{category_detected}/" + file.filename
                    await file.save(filePath)

                    os.system(f"cp {home}/tasdatabase/{game_detected}/{base_category}/*.tas {home}/UniversalClassicTas/CelesteTAS/TAS")
                    try:
                        os.system(f"cp {home}/tasdatabase/{game_detected}/{category_detected}/*.tas {home}/UniversalClassicTas/CelesteTAS/TAS")
                    except:
                        await message.channel.send("This category doesn't exist for this game (yet?)")
                        return

                    with open(filePath, 'r') as f:
                        data=f.read()
                        inputs=list(map(int,data[data.index("]")+1:].split(',')[:-1]))
                        framecount=len(inputs)-1
                        dashnum=0
                        for i in inputs:
                            if i&32:
                                dashnum+=1

                    

                    embed = discord.Embed(colour=0xffff00)
                    embed.colour = 0xffff00
                    embed.title = f"{int(file.filename[3:-4])*100}m - Playback in progress..."
                    embed.add_field(name="Level frames", value=framecount)
                    embed.add_field(name="Total dashes", value=dashnum)
                    embed.add_field(name="Game", value=game_detected.capitalize())
                    embed.add_field(name="Category", value=category_detected.capitalize())

                    
                    msg = await message.channel.send(embed=embed)
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(None, run)

                    if result is None:
                        await msg.send("There was a death while executing this TAS, aborting.")
                        return
                
                    newtime = datetime.strptime(result.decode("utf-8").split("(")[0][:-1][:10], "%M:%S.%f")

                    delta = oldtime-newtime

                    newtime_str = datetime.strftime(newtime, "%M:%S.%f")
                    
                
                    embed.colour = 0x32CD32
                    embed.title = f"{int(file.filename[3:-4])*100}m - Playback finished!"
                    embed.add_field(name="Final time", value=f"{newtime_str}")
                    embed.add_field(name="Time saved", value=f"{delta}")

                    await msg.edit(embed=embed)

                    force = False

                    if "--force" in message.content and message.author.guild_permissions.manage_channels:
                        force = True
                        

                    if delta <= timedelta(0) and not force:
                        await msg.channel.send(f"This file doesn't save time in {game_detected} {category_detected} and will not be uploaded!")
                        return
                    updateAndCommit(filePath, game_detected, category_detected)
                    await msg.channel.send(f"The files were uploaded to the github!")


def setup(bot):
    bot.add_cog(Tas(bot))
