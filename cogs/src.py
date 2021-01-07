from discord.ext import commands
from discord.ext import tasks
import discord
import aiohttp
import json
from dataclasses import dataclass


@dataclass
class Run:
    link: str
    categoryName: str
    player: str
    game: str
    igt: int
    rta: int
    runType: str

    @staticmethod
    def from_json(runs_json, game) -> list:

        runs = []

        for run in runs_json['data']:

            for key, value in run.items():
                if key == 'weblink':
                    link = value
                if key == 'level':
                    runType = 'categories'
                    if value:
                        runType = 'levels'
                        categoryID = value
                if key == 'category':
                    if runType == 'categories':
                        categoryID = value
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"https://www.speedrun.com/api/v1/{runType}/{categoryID}") as r:
                            if r.status == 200:
                                categoryRequest = await r.json()

                    categoryName = categoryRequest['data']['name']
                if key == 'players':
                    if value[0]['rel'] == 'guest':
                        player = value[0]['name']
                    else:
                        async with aiohttp.ClientSession() as session:
                            async with session.get(value[0]['uri']) as r:
                                if r.status == 200:
                                    nameRequest = await r.json()
                        player = nameRequest['data']['names']['international']
                if key == 'times':
                    igt = value['ingame_t']
                    rta = value['realtime_t']

            runs.append(Run(link, categoryName, player, game, igt, rta, runType))

        return runs

class Speedrun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.games = {'4d7e7z67': "CELESTE Classic", '369pokl1': "CELESTE Mods"}
        self.sent_runs = []
        self.src_update.start()


    @tasks.loop(minutes=1.0)
    async def src_update(self):

        # hardcoding this idc
        channel = self.bot.get_guild(495648733057253388).get_channel(699670465907523645)

        all_runs = []
        for game in self.games.keys():
            runs_json = None
            async with aiohttp.ClientSession() as session:
                async with session.get(f'https://www.speedrun.com/api/v1/runs?game={game}&status=new&max=200') as r:
                    if r.status == 200:
                        runs_json = await r.json()

            all_runs += Run.from_json(runs_json, self.games[game])

        if len(all_runs) == 0:
            return
	
        print(all_runs)

        new_runs = [i for i in all_runs if i not in self.sent_runs]
        
        self.sent_runs = all_runs

        for run in new_runs:
            
            # sorry but this works and I don't want to have stuff like 00:01:59
            minutes, seconds = divmod(run.igt, 60)
            seconds, milliseconds = divmod(seconds*1000, 1000)
            hours, minutes = divmod(minutes, 60)
            hours = "" if hours == 0 else str(int(hours)) + ":"
            milliseconds = "" if milliseconds == 0 else "." + f"{int(milliseconds):03d}"
            
            embed_dict = {
                "title": "Individual Level" if run.runType == "levels" else run.game,
                "description": f"{run.categoryName} in {hours}{int(minutes):02d}:{int(seconds):02d}{milliseconds} by {run.player}",
                "url": run.link,
                "color": 16711680,
                "fields": [
                    {
                    "name": "Has Real Time?",
                    "value": "No" if run.rta == 0 else "Yes"
                    }
                ]
            }

            embed = discord.Embed.from_dict(embed_dict)
            await channel.send(embed=embed)    

    @src_update.before_loop
    async def before_update(self):
        print('waiting...')
        await self.bot.wait_until_ready()


def setup(bot):
    bot.add_cog(Speedrun(bot))
