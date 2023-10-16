import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime
from database.database_manager import delete_old_translations, edit_guild, retrieve_guild_membership, delete_translation_settings

class MaintainCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_old_translations_loop.start()

    def cog_unload(self):
        self.delete_old_translations_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Maintain running")
        await self.check_membership_loop()

    @tasks.loop(hours=6)
    async def delete_old_translations_loop(self):
        for guild in self.bot.guilds:
            guild_id = guild.id
            await delete_old_translations(guild_id)
            print(f'Deleted old translations for guild ID: {guild_id}')

    @delete_old_translations_loop.before_loop
    async def before_delete_old_translations_loop(self):
        print('Waiting until bot is ready to start delete_old_translations_loop...')
        await self.bot.wait_until_ready()

    @tasks.loop(hours=12)
    async def check_membership_loop(self):
        for guild in self.bot.guilds:
            guild_id = guild.id
            membership_details = await retrieve_guild_membership(guild_id)
            if membership_details:
                expiry_timestamp = membership_details.get("expiry_date")
                if expiry_timestamp:
                    expiry_date = datetime.utcfromtimestamp(expiry_timestamp)
                    if datetime.utcnow() > expiry_date:
                        result = await edit_guild(guild_id, membership_type='free', expiry_date=None)
                        print(f'Updated membership for guild ID: {guild_id}, result: {result}')
  
                        # Delete translation settings for the guild
                        await delete_translation_settings(guild_id)
  
                        # Update the channels_to_listen in the Translator cog
                        translator_cog = self.bot.get_cog('Translator')
                        if translator_cog:
                            await translator_cog.update_channels_to_listen()
  
                    else:
                        print(f'Membership is still active for guild ID: {guild_id}')
                else:
                    print(f'No expiry date found for guild ID: {guild_id}')
            else:
                print(f'No membership details found for guild ID: {guild_id}')

    @check_membership_loop.before_loop
    async def before_check_membership_loop(self):
      print('Waiting until bot is ready to start check_membership_loop...')
      await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(MaintainCog(bot))
