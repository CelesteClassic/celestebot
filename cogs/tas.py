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
from bs4 import BeautifulSoup
import re
import string

VERIFICATION_CHANNEL_ID = 1121592306936578162

class TasDatabase:
    def __init__(self):
        home = Path.home()
        home = Path("..").resolve()
        self.gitPath=home/'tasdatabase'
        self.repo = git.Repo(self.gitPath)
        self.repo.git.pull()
        self.jsonPath=self.gitPath/'database.json'
        with open(self.jsonPath,'r') as f:
            self.data=json.load(f)

    async def add_category(self, game, category, category_full_name, level_names):
        #level_names is a list of pairs of (level_name, file_name)
        self.data[game][category]=[]
        for level_name,file_name in level_names:
            self.data[game][category].append({
                "name": level_name,
                "file": file_name,
                "frames": None
            })
        self.data["fulltime"][game][category] = None
        await self.write_db()
        category_path = self.gitPath/game/category
        category_path.mkdir()
        with open("category_index.html") as f:
            category_html = f.read()

        category_html = category_html.replace("{game_name}" ,game)
        category_html = category_html.replace("{zip_name}" ,f"Full{game.capitalize()}{category.capitalize()}.zip")
        category_html = category_html.replace("{category_name}" ,category_full_name)
        with open(category_path / "index.html", "w") as f:
            f.write(category_html)

        with open(self.gitPath/game/"index.html", "r+") as f:
            game_html = f.read()
            soup = BeautifulSoup(game_html, features = "lxml")

            new_tag = soup.new_tag("a", href=category)
            new_tag.string = category_full_name

            content_div = soup.find("div", {"class": "content"})
            content_div.insert(-2, new_tag)
            content_div.append(soup.new_tag("br"))

            f.truncate(0)
            f.seek(0)
            f.write(soup.prettify())
        self.repo.index.add([category_path / "index.html", self.gitPath/game/"index.html", self.jsonPath])



    async def add_game(self, game, game_full_name):
        self.data[game]={}
        self.data["fulltime"][game] = {}
        await self.write_db()

        game_path = self.gitPath/game
        game_path.mkdir()
        with open("game_index.html") as f:
            game_html = f.read()

        game_html = game_html.replace("{game_name}", game)

        with open(game_path/"index.html", "w") as f:
            f.write(game_html)


        with open(self.gitPath/"index.html", "r+") as f:
            root_html = f.read()
            soup = BeautifulSoup(root_html, features = "lxml")

            link_tag = soup.find(string = re.compile("Mods")).find_next(["a", "div"])

            # insert the new game in the correct place alphabetically
            new_tag = soup.new_tag("a", href = game)
            new_tag.string = game_full_name
            while link_tag.name == "a":
                if game < link_tag["href"]:
                    link_tag.insert_before(new_tag, soup.new_tag("br"), "\n")
                    break
                link_tag = link_tag.find_next(["a", "div"])
            else:
                # if the new game is last alphabetically, insert it after the last game
                link_tag = link_tag.find_previous("a").find_next("br")
                link_tag.insert_after("\n", new_tag, soup.new_tag("br"))

            f.truncate(0)
            f.seek(0)
            f.write(soup.prettify())

        self.repo.index.add([self.jsonPath, self.gitPath/"index.html", game_path, game_path/"index.html"])

    async def write_db(self):
        with open(self.jsonPath,'w') as f:
            json.dump(self.data, f, indent=4)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            return

        #if there was an error - reset the working tree
        print("resetting the repo")
        self.repo.git.reset("--hard")
        self.repo.git.clean("-df")



# shoutouts to gonen
async def updateAndCommit(tasfile, inputs, game, category, author):
    fileName = tasfile.filename

    async with TasDatabase() as tasdatabase:
        framecount=len(inputs)-1
        dashnum=0
        jumpnum=0
        for i in inputs:
            if i & 0x20:
                dashnum += 1
            elif i & 0x10:
                jumpnum += 1


        lvl_index = int(fileName.replace(".tas", "")[3:])
        lvl_name = str(lvl_index) + '00m'

        change={}
        for lvl in tasdatabase.data[game][category]:
            if lvl['file']==fileName or lvl['name'] == lvl_name:
                change=lvl

        if not change:
            change = tasdatabase.data[game][category][lvl_index-1]

        oldframes = framecount

        if change['file'] == None:
            change['file'] = fileName
        else:
            oldframes=change['frames']


        change['frames']=framecount
        if 'dashes' in category:
            change['dashes']=dashnum
        if 'jumps' in category:
            change['jumps']=jumpnum

        await tasdatabase.write_db()

        rootPath = os.path.join(tasdatabase.gitPath, game, category)

        await tasfile.save(os.path.join(rootPath,fileName))



        zipPath=os.path.join(rootPath,f"Full{game.capitalize()}{category.capitalize()}.zip")
        with zipfile.ZipFile(zipPath,"w") as zf:
            for file in os.listdir(rootPath):
                if file.endswith(".tas"):
                    zf.write(os.path.join(rootPath,file),os.path.join("TAS",file))

        tasdatabase.repo.index.add([os.path.join(rootPath,fileName), zipPath, tasdatabase.jsonPath])

        if oldframes:
            commit_msg=f'updated {game} {category} {change["name"]} to be {framecount}f ({int(framecount)-int(oldframes):+}f) (automated)'
        else:
            commit_msg=f'added {game} {category} {change["name"]} ({framecount}f) (automated)'

        author = git.Actor(author, "celestebot@celesteclassic.github.io")
        tasdatabase.repo.index.commit(commit_msg, author=author)
        # tasdatabase.repo.remotes.origin.push()
        return commit_msg.removesuffix(" (automated)")

async def addGameToRepo(game, game_full_name, author):
    async with TasDatabase() as tasdatabase:
        await tasdatabase.add_game(game, game_full_name)
        commit_msg=f'added new game {game} (automated)'
        author = git.Actor(author, "celestebot@celesteclassic.github.io")
        tasdatabase.repo.index.commit(commit_msg, author=author)
        tasdatabase.repo.remotes.origin.push()

async def addCategory(game, category, category_full_name, level_name_data, author):
    level_names = []
    for line in level_name_data.splitlines():
        level_name, file_name = line.rsplit(maxsplit=1)
        level_names.append([level_name, file_name])


    async with TasDatabase() as tasdatabase:
        await tasdatabase.add_category(game, category, category_full_name, level_names)
        commit_msg=f'added new category {category} to {game} (automated)'
        author = git.Actor(author, "celestebot@celesteclassic.github.io")
        tasdatabase.repo.index.commit(commit_msg, author=author)
        tasdatabase.repo.remotes.origin.push()


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
    if "]" in data:
        input_str = data[data.index("]")+1:]
    else:
        input_str = data
    input_str = input_str.rstrip(string.whitespace + ",")
    return list(map(int,input_str.split(',')))

@dataclass
class TasSubmission:
    attachment: discord.Attachment
    inputs: list[int]
    game: str
    category: str
    author: str
    level: int
    message: discord.Message

    def __str__(self):
        return f"{self.game}, {self.category} {self.level}00m by {self.author} in {len(self.inputs)-1}f"
class Tas(commands.Cog):

    def is_tas_verifier(self, ctx):
        role = discord.utils.get(ctx.guild.roles, name="TAS Verifier")
        return ctx.author.guild_permissions.manage_channels or role in ctx.author.roles
        #return role in ctx.author.roles
    def __init__(self, bot):
        self.bot = bot
        self.submitted_tases = []


    @commands.command(aliases=["updatetas", "sendtas"])
    async def uploadtas(self, ctx, game, category):
        if len(ctx.message.attachments) == 0:
            await ctx.send("Please include at least one attachment with the message")
            return
        for attachment in ctx.message.attachments:
            try:
                data = (await attachment.read()).decode("utf-8")
                inputs = process_inputs(data)
                level = int(attachment.filename.replace(".tas", "")[3:])
                if (self.is_tas_verifier(ctx)):
                    msg = await updateAndCommit(attachment, inputs, game, category, ctx.author.name)
                    await ctx.send(f"{msg} (probably)")
                else:
                    new_sub = TasSubmission(attachment, inputs, game, category, ctx.author.name, level, ctx.message)

                    self.submitted_tases.append(new_sub)
                    await ctx.send(f"TAS for {new_sub} sent for verification!")
                    embed = discord.Embed(title="New TAS waiting for verification",
                            description=str(new_sub) +
                                        f"\n[Click here to download the .tas]({attachment.url})",
                            color=0x00E436)
                    embed.set_footer(text=f"To verify this TAS, use: !verifytas {len(self.submitted_tases)-1}")
                    await ctx.guild.get_channel(VERIFICATION_CHANNEL_ID).send(embed=embed)
            except:
                traceback.print_exc()
                await ctx.send(f"Something went wrong while uploading the TAS file {attachment.filename}! (tell cominixo)")

    @commands.command(aliases=["approvetas"])
    async def verifytas(self, ctx, id: int):
        if (self.is_tas_verifier(ctx)):
            if (id < len(self.submitted_tases)):
                tas = self.submitted_tases[id]
                if (tas):
                    try:
                        await updateAndCommit(tas.attachment, tas.inputs, tas.game, tas.category, tas.author)
                        await ctx.send(f"TAS for {tas} has been approved!")
                        await tas.message.reply(f"TAS for {tas} has been approved and uploaded (probably)!")
                        self.submitted_tases[id] = None
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

    @commands.command()
    async def tasaddmod(self, ctx, game, full_game_name):
        if (self.is_tas_verifier(ctx)):
            try:
                await addGameToRepo(game, full_game_name, ctx.author.name)
                await ctx.send("Mod added to db (probably)!")
            except:
                traceback.print_exc()
                await ctx.send("Something went wrong while adding the mod (tell cominixo)")


    @commands.command()
    async def tasaddcategory(self, ctx, game, category, full_category_name):
        if len(ctx.message.attachments) > 0:
            if (self.is_tas_verifier(ctx)):
                try:
                    level_name_data = (await ctx.message.attachments[0].read()).decode('utf-8')
                    await addCategory(game, category, full_category_name, level_name_data, ctx.author.name)
                    await ctx.send("category added to db (probably)!")
                except:
                    traceback.print_exc()
                    await ctx.send("Something went wrong while adding the category (tell cominixo)")
        else:
            await ctx.send("Please include a file containing the level and corrosponding file names")



async def setup(bot):
    await bot.add_cog(Tas(bot))
