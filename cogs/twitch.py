import os
import traceback
import concurrent.futures
import functools
import cogs.streamtracker
import discord
from discord.ext import commands, tasks
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.object.eventsub import StreamOnlineEvent, StreamOfflineEvent
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.type import AuthScope
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
        self.twitch_names = []
        for n in data:
            string = n.replace("\n", "").split("|")
            self.twitch_names.append(string[0])
            self.messages[string[0]] = {"live": False, "noti_sent": False, "noti_string": string[1], "ingame_name": string[2], "last_msg": 0}
    
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
            if type(stream) == type(None):
                game = "Legion TD 2"
                started_at = ""
            else:
                game = stream.game_name
                started_at = str(stream.started_at)
            if game == "Legion TD 2":
                self.messages[event_data.event.broadcaster_user_name]["live"] = True
                self.messages[event_data.event.broadcaster_user_name]["noti_sent"] = False
                self.messages[event_data.event.broadcaster_user_name]["stream_started_at"] = started_at
                print(f'{event_data.event.broadcaster_user_name} is live!')
            else:
                print(f'{event_data.event.broadcaster_user_name} is live but not playing ltd2.')
        except Exception:
            traceback.print_exc()
    
    async def on_offline(self, event_data: StreamOfflineEvent):
        try:
            print(f'{event_data.event.broadcaster_user_name} is done streaming.')
            self.messages[event_data.event.broadcaster_user_name]["live"] = False
        except Exception:
            traceback.print_exc()
    
    @tasks.loop(seconds=3.0)
    async def message(self):
        for streamer in self.messages:
            try:
                if self.messages[streamer]["live"] and self.messages[streamer]["noti_sent"] == False:
                    if self.messages[streamer]["ingame_name"] != " ":
                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            print(await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, self.messages[streamer]["ingame_name"], stream_started_at=self.messages[streamer]["stream_started_at"])) + " session started.")
                            pool.shutdown()
                        with open("sessions/session_"+self.messages[streamer]["ingame_name"]+".json", "r") as f:
                            session = json.load(f)
                            f.close()
                        end_string = f'Start elo: {session["int_elo"]} {util.get_ranked_emote(session["int_elo"])}'
                    else:
                        end_string = ""
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.send(f'{streamer} is live! {self.messages[streamer]["noti_string"]}\n{end_string}\nhttps://www.twitch.tv/'+streamer)
                    self.messages[streamer]["noti_sent"] = True
                    self.messages[streamer]["last_msg"] = message.id
                elif self.messages[streamer]["noti_sent"] and self.messages[streamer]["live"] == False:
                    print("editing message")
                    if os.path.isfile("sessions/session_" + self.messages[streamer]["ingame_name"] + ".json"):
                        with open("sessions/session_"+self.messages[streamer]["ingame_name"]+".json", "r") as f:
                            session = json.load(f)
                            f.close()
                        end_string = (f'Start Elo: {session["int_elo"]} {util.get_ranked_emote(session["int_elo"])}\n'
                            f'End elo: {session["current_elo"]} {util.get_ranked_emote(session["current_elo"])}'
                            f'{session["current_wins"]-session["int_wins"]}W-{session["current_losses"]-session["int_losses"]}L')
                        os.remove("sessions/session_" + self.messages[streamer]["ingame_name"] + ".json")
                    else:
                        end_string = ""
                    self.messages[streamer]["noti_sent"] = False
                    message_id = self.messages[streamer]["last_msg"]
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.fetch_message(message_id)
                    await message.edit(content=f'{streamer} stopped streaming.\n{end_string}')
            except Exception:
                traceback.print_exc()
    
    @commands.command()
    async def start(self, ctx:commands.Context):
        print("starting twitch eventsub")
        self.message.start()
        try:
            self.twitchclient = await Twitch(secret_file.get("twitchappid"), secret_file.get("twitchsecret"))
            users = self.twitchclient.get_users(logins=self.twitch_names)
            self.eventsub = EventSubWebhook(callback_url="https://twitch.drachbot.site/", port=8000, twitch=self.twitchclient)
            await self.eventsub.unsubscribe_all()
            #self.eventsub.wait_for_subscription_confirm = False
            self.eventsub.start()
            async for u in users:
                try:
                    print(u.id, u.display_name)
                    sub_id = await self.eventsub.listen_stream_online(u.id, self.on_online)
                    #print(sub_id)
                    sub_id2 = await self.eventsub.listen_stream_offline(u.id, self.on_offline)
                    #print(sub_id2)
                    #print(self.eventsub.secret)
                except Exception:
                    traceback.print_exc()
                    print(u.display_name + " failed")
            print("Eventsub initialized.")
        except Exception:
            traceback.print_exc()
    
    @commands.command()
    async def refresh_streamers(self, ctx: commands.Context):
        with open("Files/streamers.txt", "r") as f:
            data = f.readlines()
            f.close()
        for n in data:
            string = n.replace("\n", "").split("|")
            if string[0] not in self.twitch_names:
                self.twitch_names.append(string[0])
                self.messages[string[0]] = {"live": False, "noti_sent": False, "noti_string": string[1], "last_msg": 0}
                users = await first(self.twitchclient.get_users(logins=[string[0]]))
                await self.eventsub.listen_stream_online(users.id, self.on_online)
                await self.eventsub.listen_stream_offline(users.id, self.on_offline)
                print(f'added {string[0]} to the eventsub')
    
    @commands.command()
    async def stop(self, ctx:commands.Context):
        if os.path.isfile("sessions/TwitchSub.json"):
            os.remove("sessions/TwitchSub.json")
        with open("sessions/TwitchSub.json", "w") as f2:
            json.dump(self.messages, f2)
        self.message.stop()
        await self.eventsub.stop()
        print("stopped eventsub")


async def setup(bot:commands.Bot):
    await bot.add_cog(TwitchHandler(bot))