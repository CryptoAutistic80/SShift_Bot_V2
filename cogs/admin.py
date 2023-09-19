import nextcord
from nextcord.ext import commands

from database.database_manager import add_verification, retrieve_guild_membership

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog ready")

    @nextcord.slash_command()
    async def setup(self, inter):
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, setup cannot proceed.')
            return
        
        await inter.response.send_message('Setup command invoked')

    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def verification(self, inter, verify_channel: str, verified_role: str):
        guild_id = inter.guild.id
        
        # Step 1: Retrieve guild membership
        guild_membership = await retrieve_guild_membership(guild_id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, setup cannot proceed.')
            return
    
        # Step 2: Add verification
        response = await add_verification(guild_id, verify_channel, verified_role)
        if response is None:
            response = ''
        response += "\nVerification setup successful."
        await inter.response.send_message(response)
    
        # Step 3: Get the verification channel
        channel = self.bot.get_channel(int(verify_channel))
        if channel is None:
            await inter.response.send_message('Verification channel not found.')
            return
    
        # Step 4: Post a friendly embed message with a "Start Verification" button
        embed = nextcord.Embed(
            title="Welcome to SShift Bot!", 
            description="Thank you for using SShift Bot! Please follow the instructions carefully to complete the verification process. We're thrilled to have you here!", 
            color=0x00ff00
        )
        view = nextcord.ui.View()
        view.add_item(nextcord.ui.Button(label="Start Verification", custom_id="start_verification", style=nextcord.ButtonStyle.primary))
        await channel.send(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Admin(bot))


