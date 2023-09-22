import re

import nextcord
from nextcord.ext import commands

from database.database_manager import add_verification, retrieve_guild_membership, upsert_reaction, delete_reactions, retrieve_reactions

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
      
    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def reaction_roles(self, inter, channel_id: str, role_name: str, description: str, emoji: str):
        guild_id = inter.guild.id
    
        # Step 1: Validate the emoji
        unicode_emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F700-\U0001F77F\U0001F780-\U0001F7FF\U0001F800-\U0001F8FF\U0001F900-\U0001F9FF\U0001FA00-\U0001FA6F\U0001FA70-\U0001FAFF\U00002702-\U000027B0\U00002639\U0000231A\U0000231B\U00002B50\U0001F004\U0001F0CF]")
        custom_emoji_pattern = re.compile("<(a)?:[a-zA-Z0-9\_]+:[0-9]+>")
        if not unicode_emoji_pattern.match(emoji) and not custom_emoji_pattern.match(emoji):
            await inter.response.send_message("Invalid emoji format.")
            return
    
        # Step 2: Create the role based on role_name
        role = await inter.guild.create_role(name=role_name)
        if role is None:
            await inter.response.send_message('Failed to create role.')
            return
    
        # Step 3: Retrieve guild membership
        guild_membership = await retrieve_guild_membership(guild_id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, setup cannot proceed.')
            return
    
        # Step 4: Update or insert the reaction role
        role_id = role.id
        response = await upsert_reaction(guild_id, channel_id, emoji, description, role_id)
        if response:
            await inter.response.send_message(response)  # This will send the error message back if there's an issue
        else:
            await inter.response.send_message("Reaction role setup successful.")
            # Fetch the Reactions cog and call the load_reactions method directly
            reactions_cog = self.bot.get_cog("Reactions")
            if reactions_cog:
                await reactions_cog.load_reactions(specific_guild_id=guild_id)
          
    @nextcord.slash_command()
    async def reset(self, inter):
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, reset cannot proceed.')
            return
    
        await inter.response.send_message('Reset command invoked. Use subcommands to perform specific reset operations.')

    @reset.subcommand()
    @commands.has_permissions(administrator=True)
    async def role_reactions(self, inter):
        await inter.response.send_message("Processing role reactions reset...")  # Immediate response
    
        guild_id = inter.guild.id
        
        # Fetch all reactions for this guild from the database
        reactions = await retrieve_reactions(guild_id)
        
        if reactions:
            # Delete the corresponding roles in Discord and the embed messages
            for channel_id_str, _, _, role_id_str in reactions:
                channel_id = int(channel_id_str)  # Convert the channel_id to integer
                channel = inter.guild.get_channel(channel_id)
                if channel:
                    # Check recent messages for bot's embeds and delete them
                    async for message in channel.history(limit=10):
                        if message.author == self.bot.user and len(message.embeds) > 0:
                            await message.delete()
    
                # Delete the role in Discord
                role_id = int(role_id_str)  # Convert the role_id to integer
                role = inter.guild.get_role(role_id)
                if role:
                    await role.delete()
                    
        # Now delete the reactions from the database
        response = await delete_reactions(guild_id)
        
        if response:
            await inter.followup.send(response)  # Send database error if there's an issue using follow-up
        else:
            await inter.followup.send("Reaction roles and corresponding roles in Discord have been reset successfully.")  # Send success message using follow-up

def setup(bot):
    bot.add_cog(Admin(bot))


