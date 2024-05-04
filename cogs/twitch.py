import os
import traceback
import concurrent.futures
import functools
import twitchAPI.type
import cogs.streamtracker
import discord
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent
import asyncio
import json

import util

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

with open("Files/streamers.txt", "r") as f:
    data = f.readlines()
    f.close()

with open("Files/json/discord_channels.json", "r") as f:
    discord_channels = json.load(f)
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
            for n in data:
                string = n.replace("\n", "").split("|")
                self.messages[string[0]] = {"live": False, "noti_sent": False, "noti_string": string[1], "ingame_name": string[2], "last_msg": 0}
        self.twitch_names = []
        for n in data:
            string = n.replace("\n", "").split("|")
            self.twitch_names.append(string[0])
    
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
            if type(stream) == type(None):
                game = "Legion TD 2"
                started_at = ""
                thumb = ""
                avatar = user.profile_image_url
            else:
                game = stream.game_name
                started_at = str(stream.started_at)
                thumb = stream.thumbnail_url
                avatar = user.profile_image_url
            if game == "Legion TD 2":
                self.messages[event_data.event.broadcaster_user_name]["live"] = True
                self.messages[event_data.event.broadcaster_user_name]["noti_sent"] = False
                self.messages[event_data.event.broadcaster_user_name]["stream_started_at"] = started_at
                self.messages[event_data.event.broadcaster_user_name]["thumbnail"] = thumb
                self.messages[event_data.event.broadcaster_user_name]["avatar"] = avatar
                print(f'{event_data.event.broadcaster_user_name} is live playing ltd2!')
        except Exception:
            traceback.print_exc()
    
    async def on_offline(self, event_data: StreamOfflineEvent):
        try:
            print(f'{event_data.event.broadcaster_user_name} is done streaming.')
            self.messages[event_data.event.broadcaster_user_name]["live"] = False
        except Exception:
            traceback.print_exc()
    
    @tasks.loop(seconds=5.0)
    async def message(self):
        for streamer in self.messages:
            try:
                if self.messages[streamer]["live"] and self.messages[streamer]["noti_sent"] == False:
                    if self.messages[streamer]["ingame_name"] != " ":
                        loop = asyncio.get_running_loop()
                        if os.path.isfile(f'sessions/session_{self.messages[streamer]["ingame_name"]}.json'):
                            os.remove(f'sessions/session_{self.messages[streamer]["ingame_name"]}.json')
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            print(await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, self.messages[streamer]["ingame_name"], stream_started_at=self.messages[streamer]["stream_started_at"])) + " session started.")
                            pool.shutdown()
                        with open("sessions/session_"+self.messages[streamer]["ingame_name"]+".json", "r") as f:
                            session = json.load(f)
                            f.close()
                        end_string = f'Start elo: {session["int_elo"]}{util.get_ranked_emote(session["int_elo"])}\n'
                    else:
                        end_string = ""
                    embed = discord.Embed(color=util.random_color(), title=f"{streamer} is live! {self.messages[streamer]["noti_string"]}",description=end_string, url='https://www.twitch.tv/'+streamer)
                    try:
                        embed.set_image(url=self.messages[streamer]["thumbnail"])
                    except KeyError: pass
                    try:
                        embed.set_thumbnail(url=self.messages[streamer]["avatar"])
                    except KeyError: pass
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.send(embed=embed)
                    self.messages[streamer]["noti_sent"] = True
                    self.messages[streamer]["last_msg"] = message.id
                elif self.messages[streamer]["noti_sent"] and self.messages[streamer]["live"] == False:
                    print("editing message")
                    if os.path.isfile("sessions/session_" + self.messages[streamer]["ingame_name"] + ".json"):
                        with open("sessions/session_"+self.messages[streamer]["ingame_name"]+".json", "r") as f:
                            session = json.load(f)
                            f.close()
                        elo_change = session["current_elo"]-session["int_elo"]
                        if elo_change >= 0:
                            elo_prefix = "+"
                        else:
                            elo_prefix = ""
                        end_string = (f'Start Elo: {session["int_elo"]} {util.get_ranked_emote(session["int_elo"])}\n'
                            f'End elo: {session["current_elo"]}{util.get_ranked_emote(session["current_elo"])}({elo_prefix}{elo_change})'
                            f'{session["current_wins"]-session["int_wins"]}W-{session["current_losses"]-session["int_losses"]}L')
                        os.remove("sessions/session_" + self.messages[streamer]["ingame_name"] + ".json")
                    else:
                        end_string = ""
                    embed = discord.Embed(color=util.random_color(), title=f"{streamer} stopped streaming.", description=end_string, url='https://www.twitch.tv/' + streamer)
                    try:
                        embed.set_thumbnail(url=self.messages[streamer]["avatar"])
                    except KeyError: pass
                    self.messages[streamer]["noti_sent"] = False
                    message_id = self.messages[streamer]["last_msg"]
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed)
            except Exception:
                traceback.print_exc()
    
    @commands.command()
    async def start(self, ctx:commands.Context):
        print("starting twitch eventsub")
        self.message.start()
        try:
            self.twitchclient = await Twitch(secret_file.get("twitchappid"), secret_file.get("twitchsecret"))
            self.eventsub = EventSubWebhook(callback_url="https://twitch.drachbot.site/", port=8000, twitch=self.twitchclient)
            self.eventsub.unsubscribe_on_stop = False
            self.eventsub.start()
            print("Eventsub started.")
            await ctx.message.add_reaction("✅")
        except Exception:
            traceback.print_exc()
            await ctx.message.add_reaction("❌")

    @commands.command()
    async def add_streamers(self, ctx: commands.Context):
        try:
            with open("Files/streamers.txt", "r") as f:
                data = f.readlines()
                f.close()
            for n in data:
                string = n.replace("\n", "").split("|")
                if string[0] not in self.twitch_names:
                    self.twitch_names.append(string[0])
                    self.messages[string[0]] = {"live": False, "noti_sent": False, "noti_string": string[1], "ingame_name": string[2], "last_msg": 0}
                    users = await first(self.twitchclient.get_users(logins=[string[0]]))
                    await self.eventsub.listen_stream_online(users.id, self.on_online)
                    await self.eventsub.listen_stream_offline(users.id, self.on_offline)
                    print(f'added {string[0]} to the eventsub')
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
    async def unsub_all(self, ctx: commands.Context):
        try:
            await self.eventsub.unsubscribe_all()
            print("unsubbed all event subscriptions")
            await ctx.message.add_reaction("✅")
        except Exception:
            await ctx.message.add_reaction("❌")
    
    @commands.command()
    async def refresh_subs(self, ctx: commands.Context):
        try:
            users = self.twitchclient.get_users(logins=self.twitch_names)
            async for u in users:
                try:
                    print(u.id, u.display_name)
                    try:
                        sub_id = await self.eventsub.listen_stream_online(u.id, self.on_online)
                    except twitchAPI.type.EventSubSubscriptionConflict:
                        print(f"{u.display_name} online event sub already exists")
                    # print(sub_id)
                    try:
                        sub_id2 = await self.eventsub.listen_stream_offline(u.id, self.on_offline)
                    except twitchAPI.type.EventSubSubscriptionConflict:
                        print(f"{u.display_name} offline event sub already exists")
                    # print(sub_id2)
                    # print(self.eventsub.secret)
                except Exception:
                    traceback.print_exc()
                    print(u.display_name + " failed")
            await ctx.message.add_reaction("✅")
            print("event subs refreshed")
        except Exception:
            traceback.print_exc()
            await ctx.message.add_reaction("❌")
    
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