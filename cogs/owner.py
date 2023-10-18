import nextcord
from nextcord.ext import commands, application_checks
from database.database_manager import edit_guild, delete_translation_settings
import datetime

# Define membership types
MEMBERSHIP_TYPE_CHOICES = {
    "Free": "free",
    "Free Trial": "free trial",
    "Premium": "premium"
}

def check_if_it_is_me(interaction: nextcord.Interaction):
    return interaction.user.id == 701381748843610163

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Owner commands loaded")

    @nextcord.slash_command(name="owner", description="Root command for owner operations.")
    @application_checks.check(check_if_it_is_me)
    async def owner(self, inter):
        await inter.response.send_message('Owner command invoked')

    @owner.subcommand()
    @application_checks.check(check_if_it_is_me)
    async def gm(self, inter: nextcord.Interaction):
        await inter.response.send_message("Morning Papa! 👋")

    @owner.subcommand()
    @application_checks.check(check_if_it_is_me)
    async def goodnight(self, inter: nextcord.Interaction):
        await inter.response.send_message("Gn Dad! 😴💤😴")
  
    @owner.subcommand()
    @application_checks.check(check_if_it_is_me)
    async def upgrade_member(
            self, inter: nextcord.Interaction,
            guild_id: str = nextcord.SlashOption(description="Enter the guild id"),
            membership_type: str = nextcord.SlashOption(choices=MEMBERSHIP_TYPE_CHOICES, description="Select the membership type"),
            days: int = nextcord.SlashOption(description="Enter the number of days")
    ):
        # Convert days to timestamp string for expiration
        expiration_timestamp = str(int(datetime.datetime.now().timestamp()) + days * 86400)

        # Call edit_guild from database_manager
        await edit_guild(guild_id, membership_type, expiration_timestamp)

        await inter.response.send_message(f'Membership for guild {guild_id} upgraded to {membership_type} for {days} days.')

    @owner.subcommand()
    @application_checks.check(check_if_it_is_me)
    async def reset_translation_channels(self, inter: nextcord.Interaction):
        failed_guilds = []  # Keep track of guilds where deletion failed
        for guild in self.bot.guilds:
            guild_id = guild.id
            try:
                await delete_translation_settings(guild_id)
            except Exception as e:
                print(f"Error deleting translation settings for guild {guild_id}: {e}")
                failed_guilds.append(guild_id)

        if failed_guilds:
            await inter.response.send_message(f'Failed to reset translation channels settings for guild(s): {", ".join(map(str, failed_guilds))}.')
        else:
            await inter.response.send_message('Translation channels settings reset for all guilds successfully.')

def setup(bot):
    bot.add_cog(Owner(bot))

