import nextcord
from nextcord.ext import commands, tasks
from database.database_manager import delete_old_translations

class MaintainCog(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.delete_old_translations_loop.start()

    def cog_unload(self):
        self.delete_old_translations_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Maintain running")

    @tasks.loop(hours=6)
    async def delete_old_translations_loop(self):
        for guild in self.client.guilds:
            guild_id = guild.id
            await delete_old_translations(guild_id)
            print(f'Deleted old translations for guild ID: {guild_id}')

    @delete_old_translations_loop.before_loop
    async def before_delete_old_translations_loop(self):
        print('Waiting until bot is ready to start delete_old_translations_loop...')
        await self.client.wait_until_ready()

def setup(client):
    client.add_cog(MaintainCog(client))