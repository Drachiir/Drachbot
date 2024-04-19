#https://discord.com/api/oauth2/authorize?client_id=1152235985053171793&permissions=1084479764544&scope=bot
#test https://discord.com/api/oauth2/authorize?client_id=1152554771820072980&permissions=67584&scope=bot
import bot
import os

if __name__ == '__main__':
    print(str(os.cpu_count()) + " CPU cores available!")
    bot.run_discord_bot()
