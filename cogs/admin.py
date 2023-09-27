import re
import time
from typing import Optional
import nextcord
from nextcord.ext import commands
from database.database_manager import (add_verification, retrieve_guild_membership, upsert_reaction, delete_reactions, retrieve_reactions,
                                       upsert_welcome_message, delete_welcome_message, retrieve_welcome_message, add_token_wl)

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
        captcha_cog = self.bot.get_cog("Captcha")
        if captcha_cog:
            await captcha_cog.send_verification_prompt(inter, verify_channel)

    
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

    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def welcome(self, inter, channel_id: str, message: str):
        guild_id = inter.guild.id

        # Add or edit the welcome message
        response = await upsert_welcome_message(guild_id, channel_id, message)
        if response:
            await inter.response.send_message(response)  # This will send the error message back if there's an issue
        else:
            await inter.response.send_message("Welcome setup successful.")
          
    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def add_token_wl(self, inter, 
                           channel_id: str, 
                           blockchain: str, 
                           wl_name: str, 
                           wl_description: str, 
                           days_until_expiry: int,  # Expecting number of days until expiry
                           total_wl_spots: int,
                           token_role_1: str, 
                           supply: Optional[int] = -1,  # New supply field with default -1
                           mint_sale_date: Optional[str] = "TBA",  # New mint sale date field with default "TBA"
                           token_role_2: Optional[str] = None):
        
        # Validate token_role_1 and token_role_2 to ensure they are integers
        if not token_role_1.isdigit() or (token_role_2 and not token_role_2.isdigit()):
            await inter.response.send_message("Invalid role ID provided. Please provide a valid integer role ID.")
            return
        
        # Calculate Unix timestamp for the expiration date
        current_time = time.time()
        expiry_date = int(current_time + days_until_expiry * 24 * 60 * 60)  # Convert days to seconds and add to current time
        str_expiry_date = str(expiry_date)  # Convert the timestamp to a string for database storage
        
        guild_id = inter.guild.id
        
        # Step 1: Add the token whitelist entry to the database
        response = await add_token_wl(guild_id, channel_id, blockchain, wl_name, wl_description, mint_sale_date, token_role_1, token_role_2, supply, str_expiry_date, total_wl_spots)
            
        # Check if the response indicates an error
        if "error" in response.lower() or "exists" in response.lower():
            await inter.response.send_message("Token WL addition unsuccessful.")
            return
        
        # Step 2: Send success message if everything went well
        await inter.response.send_message("Token whitelist entry added successfully.")
      

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
          
    @reset.subcommand()
    @commands.has_permissions(administrator=True)
    async def welcomes(self, inter):
        guild_id = inter.guild.id
        
        # Delete the welcome message for this guild
        response = await delete_welcome_message(guild_id)
        
        if response:
            await inter.response.send_message(response)  # Send database error if there's an issue
        else:
            await inter.response.send_message("Welcome message has been reset successfully.")  # Send success message
          

def setup(bot):
    bot.add_cog(Admin(bot))