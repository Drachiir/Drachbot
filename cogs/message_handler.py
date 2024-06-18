import asyncio
import concurrent.futures
import functools
import traceback
import discord
from discord.ext import commands
import legion_api

def handle_response(message, author) -> str:
    p_message = message.lower()
    if '!elo fine' in p_message:    return ":eggplant:"
    if 'julian' in p_message:       return 'julian sucks'
    if 'penny' in p_message:        return 'penny sucks'
    if 'green' in p_message:        return '<:green:1136426397619978391> & aggressive'
    if 'kidkpro' in p_message:      return ':eggplant:'
    if 'widderson' in p_message:    return ':banana:'
    if 'ofma' in p_message:         return ':a: :b:'
    if 'drachir' in p_message:      return '<:GK:1161013811927601192>'
    if 'shea' in p_message:         return 'sister? <:sheastare:1121047323464712273>'
    if 'aviator' in p_message:      return '<:aviator:1180232477537738944>'
    if 'lucy' in p_message:         return 'snail angle <:Dice:1180232938399469588>'
    if 'kingdan' in p_message:      return "like its the most fun i've had playing legion pretty much"
    if 'genom' in p_message:        return ":rat:"
    if 'quacker' in p_message:      return ":duck: quack"
    if 'toikan' in p_message:       return "nyctea, :older_man:"
    if 'jokeonu' in p_message:      return "look dis brah, snacc <:snacc:1225281693393616936>"
    if 'mrbuzz' in p_message:       return "(On his smurf)"
    if 'nyctea' in p_message:       return "toikan,"
    if 'modabuse' in p_message:     return "Julian, do not talk to me. <:Stare:1148703530039902319>"
    if 'lwon' in p_message:         return "<:AgentEggwon:1215622131187191828> fucking teamates, nothing you can do"
    if '!github' in p_message:      return 'https://github.com/Drachiir/Drachbot'
    if '!novaupdate' in p_message and str(author) == 'drachir_':    return legion_api.pull_games_by_id(message.split('|')[1],message.split('|')[2])
    if '!update' in p_message:    return 'thanks ' + str(author) + '!'
    # if '!script' and str(author) == "drachir_":
    #     path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/"
    #     path3 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/"
    #     games = sorted(os.listdir(path3))
    #     for i, x in enumerate(games):
    #         print(str(i+1) + " out of " + str(len(games)))
    #         path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + x + "/gamedata/"
    #         try:
    #             print(path2)
    #             games2 = os.listdir(path2)
    #         except FileNotFoundError:
    #             print("not found")
    #             continue
    #         for game in games2:
    #             file_name = os.path.join(path2, game)
    #             try:
    #                 shutil.copy(file_name, path1)
    #             except shutil.Error:
    #                 continue

class Message_handler(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    async def send_message(self, message, user_message, username):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            try:
                response = await loop.run_in_executor(pool, functools.partial(handle_response, user_message, username))
                if type(response) == discord.Embed:
                    await message.channel.send(embed=response)
                else:
                    await message.channel.send(response)
            except Exception:
                pass
                
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == self.client.user.id:
            return
        if '!' in message.content:
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
        else:
            return
        await self.send_message(message, user_message, username)

async def setup(bot:commands.Bot):
    await bot.add_cog(Message_handler(bot))