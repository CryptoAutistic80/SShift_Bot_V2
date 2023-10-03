import nextcord
from nextcord.ext import commands

class Whitelists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Whitelists ready")

def setup(bot):
    bot.add_cog(Whitelists(bot))
