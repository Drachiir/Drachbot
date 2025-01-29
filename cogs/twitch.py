import os
import platform
import traceback
import concurrent.futures
import functools
from datetime import datetime

import cogs.streamtracker
import discord
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent, ChannelUpdateEvent
import asyncio
import json

import legion_api
import util

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

class TwitchHandler(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.twitchclient: Twitch | None = None
        self.eventsub: EventSubWebhook | None = None
        if os.path.isfile("sessions/TwitchSub.json"):
            with open("sessions/TwitchSub.json", "r") as f:
                self.messages: dict = json.load(f)
        else:
            self.messages: dict = {}
        self.twitch_names = []
        if os.path.isfile("Files/streamers.json"):
            with open("Files/streamers.json", "r") as f:
                streamers = json.load(f)
            for streamer in streamers:
                active_flag = streamers[streamer]["active_flag"]
                ingame_ids = streamers[streamer]["player_ids"]
                self.messages[streamer] = {
                    "live": False,
                    "noti_sent": False,
                    "noti_string": active_flag,
                    "ingame_ids": ingame_ids,
                    "last_msg": {}
                }
                self.twitch_names.append(streamer)
    
    async def cog_check(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            return True
        else:
            return False

    def cog_unload(self):
        self.message.cancel()
    
    async def on_online(self, event_data: StreamOnlineEvent):
        try:
            stream = await first(self.twitchclient.get_streams(user_id=[event_data.event.broadcaster_user_id]))
            user = await first(self.twitchclient.get_users(user_ids=[event_data.event.broadcaster_user_id]))
            if stream is None:
                print(f"Online event for {event_data.event.broadcaster_user_name} but no stream data, trying again in 30 seconds")
                await asyncio.sleep(30)
                stream = await first(self.twitchclient.get_streams(user_id=[event_data.event.broadcaster_user_id]))
            streamer_name = event_data.event.broadcaster_user_name
            if stream is not None:
                game = stream.game_name
                started_at = str(stream.started_at)
                title = stream.title
                avatar = user.profile_image_url
                if game == "Legion TD 2":
                    self.messages[streamer_name]["live"] = True
                    self.messages[streamer_name]["noti_sent"] = False
                    self.messages[streamer_name]["stream_started_at"] = started_at
                    self.messages[streamer_name]["avatar"] = avatar
                    self.messages[streamer_name]["title"] = title
                    print(f'{streamer_name} is live playing ltd2!')
            else:
                print(f"Online event for {streamer_name} but no stream data")
        except Exception:
            traceback.print_exc()
    
    async def on_offline(self, event_data: StreamOfflineEvent):
        try:
            streamer_name = event_data.event.broadcaster_user_name
            print(f'{streamer_name} is done streaming.')
            self.messages[streamer_name]["live"] = False
        except Exception:
            traceback.print_exc()
    
    async def on_change(self, event_data: ChannelUpdateEvent):
        try:
            stream = await first(self.twitchclient.get_streams(user_id=[event_data.event.broadcaster_user_id]))
            user = await first(self.twitchclient.get_users(user_ids=[event_data.event.broadcaster_user_id]))
            if type(stream) == type(None):
                pass
            else:
                started_at = str(stream.started_at)
                title = stream.title
                avatar = user.profile_image_url
                streamer_name = event_data.event.broadcaster_user_name
                if event_data.event.category_name == "Legion TD 2" and not self.messages[streamer_name]["live"] and started_at != "":
                    self.messages[streamer_name]["live"] = True
                    self.messages[streamer_name]["noti_sent"] = False
                    self.messages[streamer_name]["stream_started_at"] = started_at
                    self.messages[streamer_name]["avatar"] = avatar
                    self.messages[streamer_name]["title"] = title
                    print(f'{streamer_name} changed to playing ltd2!')
                elif event_data.event.category_name != "Legion TD 2" and self.messages[streamer_name]["live"] and started_at != "":
                    self.messages[streamer_name]["live"] = False
                    print(f'{streamer_name} stopped playing ltd2!')
                # elif event_data.event.category_name == "Legion TD 2" and self.messages[event_data.event.broadcaster_user_name]["live"]:
                #     self.messages[event_data.event.broadcaster_user_name]["update_title"] = True
                #     self.messages[event_data.event.broadcaster_user_name]["title"] = title
        except Exception:
            traceback.print_exc()
    
    @tasks.loop(seconds=5.0)
    async def message(self):
        with open("Files/streamers.json", "r") as f:
            streamers = json.load(f)
        streamers_changed = False
        for streamer in self.messages:
            try:
                if self.messages[streamer]["live"] and self.messages[streamer]["noti_sent"] == False:
                    rank = 0
                    end_string = ""
                    if self.messages[streamer]["ingame_ids"]:
                        loop = asyncio.get_running_loop()
                        try:
                            with concurrent.futures.ThreadPoolExecutor() as pool:
                                for i, player_id in enumerate(self.messages[streamer]["ingame_ids"]):
                                    api_profile = await loop.run_in_executor(legion_api.getprofile, player_id)
                                    player_name = api_profile["playerName"]
                                    if streamers[streamer]["display_names"][i] != player_name:
                                        streamers[streamer]["display_names"][i] = player_name
                                        streamers_changed = True
                                pool.shutdown()
                        except Exception:
                            traceback.print_exc()
                            print(f"Something wrong getting the name from {streamer}")
                            continue
                        accounts = self.messages[streamer]["ingame_ids"]
                        for acc in accounts:
                            if os.path.isfile(f'sessions/session_{acc}.json'):
                                mod_date = datetime.utcfromtimestamp(os.path.getmtime(f'sessions/session_{acc}.json'))
                                date_diff = datetime.now() - mod_date
                                if platform.system() == "Linux":
                                    minutes_diff = date_diff.total_seconds() / 60
                                else:
                                    minutes_diff = date_diff.total_seconds() / 60 - 60
                                if minutes_diff > 60:
                                    os.remove(f'sessions/session_{acc}.json')
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        print(await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, stream_started_at=self.messages[streamer]["stream_started_at"])) + " session started.")
                                        pool.shutdown()
                                else:
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, update=True))
                                        pool.shutdown()
                            else:
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    print(await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, stream_started_at=self.messages[streamer]["stream_started_at"])) + " session started.")
                                    pool.shutdown()
                            try:
                                with open("sessions/session_"+acc+".json", "r") as f:
                                    session = json.load(f)
                                    f.close()
                            except FileNotFoundError:
                                continue
                            session["live"] = True
                            rank = session["int_elo"]
                            with open("sessions/session_" + acc + ".json", "w") as f:
                                json.dump(session, f)
                                f.close()
                            end_string = f'Start elo: {session["int_elo"]}{util.get_ranked_emote(session["int_elo"])} {session["int_rank"]}\n'
                    if self.messages[streamer]["noti_string"] == "X" or (rank < 2000 and rank):
                        self.messages[streamer]["noti_sent"] = True
                        return
                    embed = discord.Embed(color=util.random_color(), title=self.messages[streamer]["title"],description=end_string, url='https://www.twitch.tv/'+streamer)
                    try:
                        embed.set_thumbnail(url=self.messages[streamer]["avatar"])
                    except KeyError:
                        pass
                    with open("Files/json/discord_channels.json", "r") as f:
                        discord_channels = json.load(f)
                        f.close()
                    for server in discord_channels["notify_channels"]:
                        guild = self.client.get_guild(discord_channels["notify_channels"][server][0])
                        channel = guild.get_channel(discord_channels["notify_channels"][server][1])
                        try:
                            elo_threshold = util.get_current_minelo(twitch=True)
                        except Exception:
                            elo_threshold = 2800
                        if (self.messages[streamer]["noti_string"] == "Y") or (rank >= elo_threshold):
                            role = guild.get_role(discord_channels["notify_channels"][server][2])
                            try:
                                mention_string = role.mention
                            except Exception:
                                mention_string = ""
                        else:
                            mention_string = ""
                        try:
                            message = await channel.send(content=f"{streamer} is live playing LTD2! {mention_string}", embed=embed)
                        except Exception:
                            print(f"Error sending message to {server} streams channel")
                            traceback.print_exc()
                            continue
                        self.messages[streamer]["last_msg"][server] = message.id
                    self.messages[streamer]["noti_sent"] = True
                elif self.messages[streamer]["noti_sent"] and self.messages[streamer]["live"] == False:
                    print("editing message")
                    end_string = ""
                    accounts = self.messages[streamer]["ingame_ids"]
                    for acc in accounts:
                        if os.path.isfile("sessions/session_" + acc + ".json"):
                            with open("sessions/session_"+acc+".json", "r") as f:
                                session = json.load(f)
                                f.close()
                            session["live"] = False
                            with open("sessions/session_"+acc+".json", "w") as f:
                                json.dump(session, f)
                                f.close()
                            mod_date = datetime.utcfromtimestamp(os.path.getmtime(f'sessions/session_{acc}.json'))
                            date_diff = datetime.now() - mod_date
                            if platform.system() == "Linux":
                                minutes_diff = date_diff.total_seconds() / 60
                            else:
                                minutes_diff = date_diff.total_seconds() / 60 - 60
                            if minutes_diff < 60:
                                elo_change = session["current_elo"]-session["int_elo"]
                                if elo_change >= 0:
                                    elo_prefix = "+"
                                else:
                                    elo_prefix = ""
                                wins = session["current_wins"]-session["int_wins"]
                                losses = session["current_losses"]-session["int_losses"]
                                try:
                                    winrate = round(wins/(wins+losses)*100)
                                except ZeroDivisionError:
                                    winrate = 0
                                end_string = (f'Start Elo: {session["int_elo"]} {util.get_ranked_emote(session["int_elo"])} {session["int_rank"]}\n'
                                    f'End elo: {session["current_elo"]}{util.get_ranked_emote(session["current_elo"])}({elo_prefix}{elo_change}) {session["current_rank"]}'
                                    f'\n{wins}W-{losses}L, WR: {winrate}%')
                            else:
                                end_string = ""
                        else:
                            end_string = ""
                    embed = discord.Embed(color=util.random_color(), title=f"{streamer} stopped streaming LTD2.", description=end_string, url='https://www.twitch.tv/' + streamer)
                    try:
                        embed.set_thumbnail(url=self.messages[streamer]["avatar"])
                    except KeyError: pass
                    self.messages[streamer]["noti_sent"] = False
                    with open("Files/json/discord_channels.json", "r") as f:
                        discord_channels = json.load(f)
                        f.close()
                    for server in self.messages[streamer]["last_msg"]:
                        message_id = self.messages[streamer]["last_msg"][server]
                        guild = self.client.get_guild(discord_channels["notify_channels"][server][0])
                        channel = guild.get_channel(discord_channels["notify_channels"][server][1])
                        message = await channel.fetch_message(message_id)
                        try:
                            await message.edit(content="", embed=embed)
                        except Exception:
                            print(f"Error editing message on {server} streams channel")
                            traceback.print_exc()
            except Exception:
                self.messages[streamer]["live"] = False
                traceback.print_exc()

        if streamers_changed:
            with open("Files/streamers.json", "w") as f:
                json.dump(streamers, f)
    
    @commands.command()
    async def start(self, ctx:commands.Context):
        print("starting twitch eventsub")
        self.message.start()
        try:
            self.twitchclient = await Twitch(secret_file.get("twitchappid"), secret_file.get("twitchsecret"))
            users = self.twitchclient.get_users(logins=self.twitch_names)
            self.eventsub = EventSubWebhook(callback_url="https://twitch.drachbot.site/", port=8000, twitch=self.twitchclient)
            await self.eventsub.unsubscribe_all()
            self.eventsub.start()
            async for u in users:
                try:
                    print(u.id, u.display_name)
                    sub_id = await self.eventsub.listen_stream_online(u.id, self.on_online)
                    # print(sub_id)
                    sub_id2 = await self.eventsub.listen_stream_offline(u.id, self.on_offline)
                    # print(sub_id2)
                    sub_id3 = await self.eventsub.listen_channel_update(u.id, self.on_change)
                    # print(self.eventsub.secret)
                except Exception:
                    traceback.print_exc()
                    print(u.display_name + " failed")
            print("Eventsub started.")
            await ctx.message.add_reaction("✅")
        except Exception:
            traceback.print_exc()
            await ctx.message.add_reaction("❌")
    
    #twitchname|ign|Y/X/
    @commands.command()
    async def add_streamer(self, ctx: commands.Context):
        try:
            text = ctx.message.content[14:].split("|")  # Assumes input format: twitchname|ign|Y/X/
            twitch_name = text[0].strip()
            ign = text[1].strip()
            active_flag = text[2].strip().upper()

            json_file = "Files/streamers.json"
            with open(json_file, "r") as f:
                data = json.load(f)

            if twitch_name in data:
                await ctx.send(f"Streamer `{twitch_name}` is already in the list.")
                return
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                player_id = await loop.run_in_executor(pool, legion_api.getid, ign)
                pool.shutdown()
            new_streamer = {
                "active_flag": active_flag,
                "display_name": ign,
                "player_ids": [player_id]
            }
            data[twitch_name] = new_streamer

            with open(json_file, "w") as f:
                json.dump(data, f, indent=4)

            if twitch_name not in self.twitch_names:
                self.twitch_names.append(twitch_name)
                self.messages[twitch_name] = {
                    "live": False,
                    "noti_sent": False,
                    "noti_string": active_flag,
                    "ingame_ids": [player_id],
                    "last_msg": {}
                }
                users = await first(self.twitchclient.get_users(logins=[twitch_name]))
                await self.eventsub.listen_stream_online(users.id, self.on_online)
                await self.eventsub.listen_stream_offline(users.id, self.on_offline)
                await self.eventsub.listen_channel_update(users.id, self.on_change)
                print(f"Added {twitch_name} to the eventsub")
            await ctx.message.add_reaction("✅")
        except Exception:
            traceback.print_exc()
            await ctx.message.add_reaction("❌")
    
    @commands.command()
    async def mock_online(self, ctx: commands.Context):
        text = ctx.message.content[13:]
        streamer = text.split(" ")[0]
        title = text.split(" ")[1]
        playerid = text.split(" ")[2]
        with open("Files/streamers.json", "r") as f:
            streamers = json.load(f)
        streamers[streamer] = {
            "active_flag": "",
            "display_names": [
                ""
            ],
            "player_ids": [
                playerid
            ]
        }
        with open("Files/streamers.json", "w") as f:
            json.dump(streamers, f)
        self.messages[streamer] = {"live": True, "noti_sent": False, "noti_string": "", "ingame_ids": [playerid], "last_msg": {}, "title": title, "stream_started_at": ""}
        
    @commands.command()
    async def mock_offline(self, ctx: commands.Context):
        text = ctx.message.content[14:]
        self.messages[text]["live"] = False
        
    @commands.command()
    async def check_online(self, ctx: commands.Context):
        try:
            username = ctx.message.content[14:]
            for streamer in self.twitch_names:
                if username == "all":
                    pass
                elif username == streamer:
                    pass
                else:
                    continue
                stream = await first(self.twitchclient.get_streams(user_login=[streamer]))
                user = await first(self.twitchclient.get_users(logins=[streamer]))
                if type(stream) == type(None):
                    game = ""
                    self.messages[streamer]["live"] = False
                    print(f'{streamer} is done streaming')
                else:
                    game = stream.game_name
                    started_at = str(stream.started_at)
                    title = stream.title
                    avatar = user.profile_image_url
                if game == "Legion TD 2":
                    self.messages[streamer]["live"] = True
                    self.messages[streamer]["noti_sent"] = False
                    self.messages[streamer]["stream_started_at"] = started_at
                    self.messages[streamer]["avatar"] = avatar
                    self.messages[streamer]["title"] = title
                    print(f'{streamer} is live playing ltd2!')
            await ctx.message.add_reaction("✅")
        except Exception:
            traceback.print_exc()
            await ctx.message.add_reaction("❌")
    
    @commands.command()
    async def stop(self, ctx:commands.Context):
        self.message.stop()
        await self.eventsub.stop()
        if os.path.isfile("sessions/TwitchSub.json"):
            os.remove("sessions/TwitchSub.json")
        with open("sessions/TwitchSub.json", "w") as f2:
            json.dump(self.messages, f2)
        print("stopped eventsub")
        await ctx.message.add_reaction("✅")
    
    @commands.command()
    async def pull_dict(self, ctx: commands.Context):
        if os.path.isfile("sessions/TwitchSubCopy.json"):
            os.remove("sessions/TwitchSubCopy.json")
        with open("sessions/TwitchSubCopy.json", "w") as f2:
            json.dump(self.messages, f2)
        print("pulled eventsub dict")
        await ctx.message.add_reaction("✅")
    
    @commands.command()
    async def push_dict(self, ctx: commands.Context):
        if os.path.isfile("sessions/TwitchSubCopy.json"):
            with open("sessions/TwitchSubCopy.json", "r") as f2:
                self.messages = json.load(f2)
            print("pushed new eventsub dict")
            await ctx.message.add_reaction("✅")
        else:
            print("TwitchSubCopy.json doesn't exist")
            await ctx.message.add_reaction("❌")

async def setup(bot:commands.Bot):
    await bot.add_cog(TwitchHandler(bot))