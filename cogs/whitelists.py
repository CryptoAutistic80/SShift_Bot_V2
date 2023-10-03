import nextcord
from nextcord.ext import commands
from database.database_manager import retrieve_all_whitelists_for_guild

# Initialize a list to store channel IDs
WHITELIST_CHANNELS = []

class Whitelists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelists = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Whitelists ready")
        await self.get_lists()

    async def get_lists(self, specific_guild_id=None):
        print("Loading whitelists...")  # Debugging print statement

        target_guilds = self.bot.guilds
        if specific_guild_id:
            guild = self.bot.get_guild(specific_guild_id)
            if guild:
                target_guilds = [guild]

        # Retrieve whitelists for the target guilds
        for guild in target_guilds:
            whitelists = await retrieve_all_whitelists_for_guild(guild.id)
            if whitelists:
                for entry in whitelists:
                    print(entry)  # Printing each retrieved entry to the console

                    # Update the WHITELIST_CHANNELS list with the channel IDs
                    if entry['channel_id'] not in WHITELIST_CHANNELS:
                        WHITELIST_CHANNELS.append(entry['channel_id'])

                    # Store the whitelist entries in a dictionary
                    self.whitelists[f'{guild.id}_{entry["wl_name"]}'] = entry

                print(f"Loaded whitelists for guild: {guild.id}")  # Debugging print statement

def setup(bot):
    bot.add_cog(Whitelists(bot))
