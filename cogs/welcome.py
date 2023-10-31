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
        
        # Send the welcome message mentioning the new user
        if welcome_channel:
            await welcome_channel.send(f"{member.mention} {message}")

def setup(client):
    client.add_cog(Welcome(client))

