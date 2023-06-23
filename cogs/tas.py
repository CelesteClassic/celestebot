from discord.ext import commands
import discord
import asyncio
import subprocess
import requests
from datetime import datetime
from datetime import timedelta
from dataclasses import dataclass

import git
import json
from distutils.dir_util import copy_tree
import zipfile
import os
import shutil
from pathlib import Path
import traceback

TAS_CHANNEL_ID = 322437582845771777
VERIFICATION_CHANNEL_ID = 322437582845771777

# shoutouts to gonen
async def updateAndCommit(tasfile, inputs, game, category, author):
    home = str(Path.home())
    gitPath=home+'/tasdatabase'
    repo = git.Repo(gitPath)
    fileName = tasfile.filename
    repo.git.pull()
    #repo.git.fetch('--all')
    #repo.git.reset('--hard', 'origin/master')

    framecount=len(inputs)-1
    dashnum=0
    jumpnum=0
    for i in inputs:
        if i & 0x20:
            dashnum += 1
        elif i & 0x10:
            jumpnum += 1

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
    if 'jumps' in category:
        change['jumps']=jumpnum

    with open(jsonPath, 'w') as f:
        json.dump(data,f,indent=4)

    rootPath = os.path.join(gitPath, game, category)

    await tasfile.save(os.path.join(rootPath,fileName))
    


    zipPath=os.path.join(rootPath,f"Full{game.capitalize()}{category.capitalize()}.zip")
    with zipfile.ZipFile(zipPath,"w") as zf:
        for file in os.listdir(rootPath):
            if file.endswith(".tas"):
                zf.write(os.path.join(rootPath,file),os.path.join("TAS",file))

    repo.index.add([os.path.join(rootPath,fileName),jsonPath,zipPath])
   
    commit_msg=f'updated {game} {category} {change["name"]} to be {framecount}f ({int(framecount)-int(oldframes):+}f) (automated)'
    author = git.Actor(author, "celestebot@celesteclassic.github.io")
    repo.index.commit(commit_msg, author=author)
    repo.remotes.origin.push()

"""def run():
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
"""

def process_inputs(data: str):
    return list(map(int,data[data.index("]")+1:].split(',')[:-1]))

@dataclass
class TasSubmission:
    attachment: discord.Attachment
    inputs: list[int]
    game: str
    category: str
    author: str
    level: int

    def __str__(self):
        return f"{self.game}, {self.category} {self.level}00m by {self.author} in {len(self.inputs)-1}f"
class Tas(commands.Cog):

    def is_tas_verifier(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name="TAS Verifier")
        #return ctx.author.guild_permissions.manage_channels or role in ctx.author.roles
        return role in ctx.author.roles
    def __init__(self, bot):
        self.bot = bot
        self.submitted_tases = []

    
    @commands.command(aliases=["updatetas", "sendtas"])
    async def uploadtas(self, ctx, game, category):
        if len(ctx.message.attachments) > 0:
            try:
                data = (await ctx.message.attachments[0].read()).decode("utf-8")
                inputs = process_inputs(data)
                level = int(ctx.message.attachments[0].filename.replace(".tas", "")[3:])
                if (self.is_tas_verifier(ctx)):
                    await updateAndCommit(ctx.message.attachments[0], inputs, game, category, ctx.author.name)
                    await ctx.send("TAS File uploaded (probably)!")
                else:
                    new_sub = TasSubmission(ctx.message.attachments[0], inputs, game, category, ctx.author.name, level)
                    
                    self.submitted_tases.append(new_sub)
                    await ctx.send("TAS File sent for verification!")
                    embed = discord.Embed(title="New TAS waiting for verification", 
                            description=str(new_sub) +
                                        f"\n[Click here to download the .tas]({ctx.message.attachments[0].url})",
                            color=0x00E436)
                    embed.set_footer(text=f"To verify this TAS, use: !verifytas {len(self.submitted_tases)-1}")
                    await ctx.guild.get_channel(VERIFICATION_CHANNEL_ID).send(embed=embed)
            except:
                traceback.print_exc()
                await ctx.send("Something went wrong while uploading the TAS file! (tell cominixo)")
        else:
            await ctx.send("Please include an attachment with the message")

    @commands.command(aliases=["approvetas"])
    async def verifytas(self, ctx, id: int):
        if (self.is_tas_verifier(ctx)):
            if (id < len(self.submitted_tases)):
                tas = self.submitted_tases[id]
                try:
                    await updateAndCommit(tas.attachment, tas.inputs, tas.game, tas.category, tas.author)
                    await ctx.guild.get_channel(TAS_CHANNEL_ID).send(f"TAS for {tas} has been approved and uploaded (probably)!")
                    del self.submitted_tases[id]
                except:
                    traceback.print_exc()
                    await ctx.send("Something went wrong while uploading the TAS file! (tell cominixo)")
            else:
                await ctx.send(f"The id {id} does not correspond to a valid TAS submission!")

    @commands.command()
    async def unverifiedtases(self, ctx):
        tas_list = ""
        for tas in self.submitted_tases:
            tas_list += f"- {tas}\n"
        
        await ctx.send("The following TASes have not yet been verified:\n" + tas_list)

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

async def setup(bot):
    await bot.add_cog(Tas(bot))
