import asyncio
import datetime
import re
import time
from typing import Annotated, Optional

import nextcord
from nextcord.ext import commands
from nextcord.ui import Button, View

from database.database_manager import (
    add_nft_wl,
    add_token_wl,
    add_verification,
    delete_reactions,
    delete_welcome_message,
    retrieve_guild_membership,
    retrieve_reactions,
    retrieve_welcome_message,
    upsert_reaction,
    upsert_welcome_message,
)



# Define the blockchain choices at the global level
BLOCKCHAIN_CHOICES = {
    "Aptos": "APTOS",
    "Optimism": "OPTIMISM",
    "Ethereum": "ETHEREUM",
    "Binance Smart Chain": "BINANCE SMART CHAIN",
    "Polygon": "POLYGON",
    "Solana": "SOLANA"
}


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

  

    @setup.subcommand(
        description=(
            "Setup a token whitelist"
        )
    )
    @commands.has_permissions(administrator=True)
    async def token_wl(
            self, inter,
            channel_mention: nextcord.TextChannel = nextcord.SlashOption(description="Mention the channel to display the whitelist claim"),
            blockchain: str = nextcord.SlashOption(
                choices=BLOCKCHAIN_CHOICES,
                description="Choose the blockchain the token lives on"
            ),
            token_name: str = nextcord.SlashOption(description="Enter the name of the token"),
            description: str = nextcord.SlashOption(description="Provide a detailed description of the token and other relevant details"),
            days_available: int = nextcord.SlashOption(description="Enter the number of days the whitelist will be available to claim"),
            total_wl_spots_available: int = nextcord.SlashOption(description="Enter the total number of whitelist spots available"),
            primary_role: nextcord.Role = nextcord.SlashOption(description="Mention the primary eligible role"),
            secondary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the secondary eligible role (optional)"),
            total_token_supply: Optional[int] = nextcord.SlashOption(description="Enter the total token supply, default TBA if left blank (optional)"),
            mint_sale_date: Optional[str] = nextcord.SlashOption(description="Enter the launch date and time in YYYY:MM:DD HH:MM format or leave blank for TBA (optional)")
    ):
        # Convert channel and role mentions to IDs
        channel_id = str(channel_mention.id)
        primary_role_id = str(primary_role.id)
        secondary_role_id = str(secondary_role.id) if secondary_role else None
    
        # Calculate Unix timestamp for the expiration date
        current_time = time.time()
        expiry_date = int(current_time + days_available * 24 * 60 * 60)
        str_expiry_date = str(expiry_date)
    
        guild_id = inter.guild.id
    
        # Convert mint_sale_date to timestamp or set to 'TBA' if blank
        if mint_sale_date:
            try:
                mint_sale_datetime = datetime.datetime.strptime(mint_sale_date, '%Y:%m:%d %H:%M')
                mint_sale_timestamp = str(int(mint_sale_datetime.timestamp()))
            except ValueError:
                await inter.response.send_message("Invalid date format. Please use YYYY:MM:DD HH:MM format.")
                return
        else:
            mint_sale_timestamp = 'TBA'
    
        # Step 1: Add the token whitelist entry to the database
        response = await add_token_wl(
            guild_id, channel_id, blockchain, token_name, total_token_supply,
            description, primary_role_id, secondary_role_id,
            str_expiry_date, total_wl_spots_available, mint_sale_timestamp
        )
    
        # Check if the response indicates an error
        if "error" in response.lower() or "exists" in response.lower():
            await inter.response.send_message("Token WL addition unsuccessful.")
            return
    
        # Step 2: Send success message if everything went well
        await inter.response.send_message("Token whitelist entry added successfully.")

      

    @setup.subcommand(
        description=(
            "Setup a NFT whitelist"
        )
    )
    @commands.has_permissions(administrator=True)
    async def nft_wl(
            self, inter,
            channel_mention: nextcord.TextChannel = nextcord.SlashOption(description="Mention the channel to display the whitelist claim"),
            blockchain: str = nextcord.SlashOption(
                choices=BLOCKCHAIN_CHOICES,
                description="Choose the blockchain the NFT collection lives on"
            ),
            wl_name: str = nextcord.SlashOption(description="Enter the name of the NFT collection"),
            wl_description: str = nextcord.SlashOption(description="Provide a detailed description of the NFT collection and other relevant details"),
            days_available: int = nextcord.SlashOption(description="Enter the number of days the whitelist will be available to claim"),
            total_wl_spots_available: int = nextcord.SlashOption(description="Enter the total number of whitelist spots available"),
            primary_role: nextcord.Role = nextcord.SlashOption(description="Mention the primary eligible role"),
            no_mints_primary: int = nextcord.SlashOption(description="Enter the number of mints for primary eligible role"),
            secondary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the secondary eligible role (optional)"),
            no_mints_secondary: Optional[int] = nextcord.SlashOption(description="Enter the number of mints for secondary eligible role (optional)"),
            tertiary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the tertiary eligible role (optional)"),
            no_mints_tertiary: Optional[int] = nextcord.SlashOption(description="Enter the number of mints for tertiary eligible role (optional)"),
            supply: Optional[int] = nextcord.SlashOption(description="Enter the total supply of NFTs, default TBA if left blank (optional)"),
            mint_sale_date: Optional[str] = nextcord.SlashOption(description="Enter the launch date and time in YYYY:MM:DD HH:MM format or leave blank for TBA (optional)")
    ):
        # Convert channel and role mentions to IDs
        channel_id = str(channel_mention.id)
        primary_role_id = f'{str(primary_role.id)}:{no_mints_primary}'
        secondary_role_id = f'{str(secondary_role.id)}:{no_mints_secondary}' if secondary_role and no_mints_secondary else None
        tertiary_role_id = f'{str(tertiary_role.id)}:{no_mints_tertiary}' if tertiary_role and no_mints_tertiary else None
        
        # Calculate Unix timestamp for the expiration date
        current_time = time.time()
        expiry_date = int(current_time + days_available * 24 * 60 * 60)
        str_expiry_date = str(expiry_date)
        
        guild_id = inter.guild.id
        
        # Convert mint_sale_date to timestamp or set to 'TBA' if blank
        if mint_sale_date:
            try:
                mint_sale_datetime = datetime.datetime.strptime(mint_sale_date, '%Y:%m:%d %H:%M')
                mint_sale_timestamp = str(int(mint_sale_datetime.timestamp()))
            except ValueError:
                await inter.response.send_message("Invalid date format. Please use YYYY:MM:DD HH:MM format.")
                return
        else:
            mint_sale_timestamp = 'TBA'
        
        # Step 1: Add the NFT whitelist entry to the database
        response = await add_nft_wl(
            guild_id, channel_id, blockchain, wl_name, supply,
            wl_description, primary_role_id, secondary_role_id, tertiary_role_id,
            str_expiry_date, total_wl_spots_available, mint_sale_timestamp
        )
        
        # Check if the response indicates an error
        if "error" in response.lower() or "exists" in response.lower():
            await inter.response.send_message("NFT WL addition unsuccessful.")
            return
        
        # Step 2: Send success message if everything went well
        await inter.response.send_message("NFT whitelist entry added successfully.")



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