import nextcord
from nextcord.ext import commands
from database.database_manager import retrieve_welcome_message  # Importing the function

class Welcome(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Welcome ready")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Fetch the welcome message details for the guild
        welcome_details = await retrieve_welcome_message(member.guild.id)

        if not welcome_details:
            # Log an error message if there's no database entry found
            print(f"No welcome message entry found for guild: {member.guild.name} (ID: {member.guild.id})")
            return

        channel_id = welcome_details["channel_id"]
        message = welcome_details["message"]

        # Fetch the channel
        welcome_channel = member.guild.get_channel(int(channel_id))

        # Create an embed message
        embed = nextcord.Embed(
            title="Welcome!",
            description=f"{member.mention} {message}",
            color=nextcord.Color.green()
        )

        # Add a thumbnail to the embed
        embed.set_thumbnail(url="attachment://move_bot.gif")

        # Send the welcome message mentioning the new user with the embed and the thumbnail image
        if welcome_channel:
            with open("media/move_bot.gif", "rb") as f:
                await welcome_channel.send(file=nextcord.File(f, "move_bot.gif"), embed=embed)

def setup(client):
    client.add_cog(Welcome(client))
