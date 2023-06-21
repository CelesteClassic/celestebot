from discord.ext import commands
from discord.ext import tasks
import discord
import requests
from config import celia_home
import asyncio, aiohttp
import os
import subprocess, shutil

gif_processing = False

class tas2gif(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def tas2gif(self, ctx, *args):

        global gif_processing
        if (gif_processing): 
            await ctx.send('A GIF is currently processing, try again later.')
            return 
        gif_processing = True

        if len(args) not in (2, 3):
            await tas2gif_error(f'Usage: !tas2gif <cartname> <level_index> [url]', ctx)
            return

        cartname = args[0]
        level = args[1]

        # Download file
        attachment_url =  args[2] if len(args) > 2  else ctx.message.attachments[0].url
        try:
            attachment_file = await fetch(attachment_url)
        except ConnectionError as e:
            await tas2gif_error(f"Error while getting TAS file (HTTP {e}).", ctx)
            return
        except:
            await tas2gif_error("Could not download TAS file!", ctx)
            return       


        # Write to disk
        tas_file = "files/" + "recordme_" + cartname + "_" + level + ".tas"      
        with open(tas_file, "w+b") as f:
            f.write(attachment_file)

        # Estimate length of TAS file    
        try:
            total_frames = attachment_file.decode("utf-8").count(",")
        except UnicodeDecodeError: 
            await tas2gif_error("Error decoding TAS file!", ctx)
            return

        max_seconds = total_frames / 30 + 2
        if max_seconds > 62:
            await tas2gif_error("TAS file exceeds the maximum of 1 minute!", ctx)
            return 

        

        # Run Celia
        shutil.copy2(tas_file, celia_home + tas_file)

        return_code = await run_celia(celia_home, cartname, max_seconds, ctx)
        if return_code == 1: return
        
        #  Linux only
        gif_path = (os.getenv("HOME") + '/.local/share/love/Celia/gifs' + '/')
        
        gif = discord.File(gif_path + 'out.gif')
        gif_processing = False
        await ctx.send(file=gif)
        await cleanup()

async def setup(bot):
    if not os.path.exists("files"): os.mkdir("files")
    if not os.path.exists(celia_home + "files"): os.mkdir(celia_home + "/files")
    await bot.add_cog(tas2gif(bot))

async def tas2gif_error(message, ctx):
    await cleanup()
    await ctx.send(message)
    return 1

async def fetch(url, params=None):
    async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200: raise ConnectionError(response.status)
                r = await response.read()
                return r

async def run_celia(celia_home, cartname, max_seconds, ctx):
    cmd = [f'{celia_home}love', '.', 'cctas', f'{cartname}', '-producegif']
    process = await asyncio.create_subprocess_exec(*cmd, cwd=celia_home)

    try:
        await asyncio.wait_for(process.wait(), max_seconds)
    except asyncio.TimeoutError:
        process.terminate()
        print("yuh")
        await tas2gif_error("TAS took much longer than expected! Malformed input?", ctx)
        return 1

    if process.returncode == 1:
        await tas2gif_error("Celia exited wrong!", ctx)
        return 1
    elif process.returncode == 2: 
        await tas2gif_error("TAS took longer than expected.", ctx)
        return 1
    elif process.returncode == 3:
        await tas2gif_error("Invalid input file.", ctx)
        return 1
    elif (process.returncode != 0): 
        await tas2gif_error("Celia exited with an error.", ctx)
        return 1

async def cleanup():
    global gif_processing
    gif_processing = False
    try:
        # Make sure there are no remaining files
        for filename in os.listdir('files/'):
             shutil.os.unlink('files/' + filename)

        for filename in os.listdir(celia_home + 'files/'):
             shutil.os.unlink(celia_home + 'files/' + filename )
    except: 
        pass