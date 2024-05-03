import traceback

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
        self.messages: dict = {}
        self.twitch_names = []
        self.notis = []
        for n in data:
            string = n.replace("\n", "")
            self.twitch_names.append(string.split("|")[0])
            self.notis.append(string.split("|")[1])
        for index, streamer in enumerate(self.twitch_names):
            self.messages[streamer] = {"live": False, "noti_sent": False, "noti_string": self.notis[index], "last_msg": 0}
        self.message.start()
        
    def cog_unload(self):
        self.message.cancel()
    
    async def on_online(self, event_data: StreamOnlineEvent):
        try:
            #stream = await first(self.twitchclient.get_streams(user_id=[event_data.event.broadcaster_user_id]))
            game_name = "Legion TD 2"
            if game_name == "Legion TD 2":
                self.messages[event_data.event.broadcaster_user_name]["live"] = True
                self.messages[event_data.event.broadcaster_user_name]["noti_sent"] = False
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
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.send(f'{streamer} is live! {self.messages[streamer]["noti_string"]}\nhttps://www.twitch.tv/'+streamer)
                    self.messages[streamer]["noti_sent"] = True
                    self.messages[streamer]["last_msg"] = message.id
                elif self.messages[streamer]["noti_sent"] and self.messages[streamer]["live"] == False:
                    print("editing message")
                    self.messages[streamer]["noti_sent"] = False
                    message_id = self.messages[streamer]["last_msg"]
                    guild = self.client.get_guild(discord_channels["toikan_streams"][0])
                    channel = guild.get_channel(discord_channels["toikan_streams"][1])
                    message = await channel.fetch_message(message_id)
                    await message.edit(content=f'{streamer} stopped streaming.')
            except Exception:
                traceback.print_exc()
    
    @commands.command()
    async def start(self, ctx:commands.Context):
        print("starting twitch eventsub")
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
                    print(sub_id)
                    sub_id2 = await self.eventsub.listen_stream_offline(u.id, self.on_offline)
                    print(sub_id2)
                    print(self.eventsub.secret)
                except Exception:
                    traceback.print_exc()
                    print(u.display_name + " failed")
            print("Evensub initialized.")
        except Exception:
            traceback.print_exc()
    
    @commands.command()
    async def stop(self, ctx:commands.Context):
        self.message.stop()
        await self.eventsub.stop()
        print("stopped eventsub")


async def setup(bot:commands.Bot):
    await bot.add_cog(TwitchHandler(bot))