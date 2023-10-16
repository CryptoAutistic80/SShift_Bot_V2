import asyncio
import datetime
import re
import time
import csv
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
    delete_whitelist_entry,
    retrieve_guild_membership,
    retrieve_reactions,
    retrieve_welcome_message,
    upsert_reaction,
    upsert_welcome_message,
    fetch_user_entries_for_wl,
    add_replace_translation_settings,
    delete_translation_settings,
    edit_guild,
    retrieve_guild_membership,
)



# Define the blockchain choices at the global level
BLOCKCHAIN_CHOICES = {
    "Aptos": "APTOS",
    "Roburna": "ROBURNA",
    "Optimism": "OPTIMISM",
    "Ethereum": "ETHEREUM",
    "Binance Smart Chain": "BINANCE SMART CHAIN",
    "Polygon": "POLYGON",
    "Solana": "SOLANA"
}

#Define membership types
MEMBERSHIP_TYPE_CHOICES = {
    "Free": "free",
    "Free Trial": "free_trial",
    "Premium": "premium"
}


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog ready")


    @nextcord.slash_command(name="owner", description="Root command for owner operations.")
    @commands.is_owner()
    async def owner(self, inter):
        await inter.response.send_message('Owner command invoked')

    @owner.subcommand()
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
      
      

    @nextcord.slash_command(name="admin", description="Root command for admin operations.")
    async def admin(self, inter):
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, cannot proceed.')
            return

        await inter.response.send_message('admin command invoked')

    @admin.subcommand()
    @commands.has_permissions(administrator=True)
    async def fetch_sheet(self, inter: nextcord.Interaction, wl_id: int):
        # Get the current guild id
        guild_id = inter.guild.id

        # Call the function to fetch user entries for the specified wl_id
        user_entries = await fetch_user_entries_for_wl(guild_id, wl_id)

        # Check if any entries were found
        if user_entries:
            # Create a CSV file to store the data
            file_name = f'wl_{wl_id}_{guild_id}.csv'
            with open(file_name, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)

                # Determine the type from the first entry (assuming all entries are of the same type)
                entry_type = user_entries[0]['type']

                # Write header row based on the type
                if entry_type == 'TOKEN':
                    writer.writerow(['User', 'Roles', 'Address'])
                else:
                    writer.writerow(['User', 'Roles', 'Address', 'Number of Mints'])

                # Process each entry and write to CSV
                for entry in user_entries:
                    user_id_str = entry['user_id'].strip('<@&>')
                    user = inter.guild.get_member(int(user_id_str))
                    user_name = f'@{user.display_name}' if user else entry['user_id']

                    role_ids_str = entry['user_roles'].split(':')
                    role_names = []
                    for role_id_str in role_ids_str:
                        role_id = int(role_id_str.strip('<@&>'))
                        role = inter.guild.get_role(role_id)
                        if role:
                            role_names.append(f'@{role.name}')
                        else:
                            role_names.append(role_id_str)
                    roles = ','.join(role_names)

                    address = entry['address']

                    if entry_type == 'TOKEN':
                        writer.writerow([user_name, roles, address])  # Write data rows for TOKEN
                    else:
                        no_mints = 'Unlimited' if entry['no_mints'] == -1 else entry['no_mints']
                        writer.writerow([user_name, roles, address, no_mints])  # Write data rows for NFT

            # Upload the file to Discord
            with open(file_name, 'rb') as file:
                await inter.response.send_message('Here is the requested data:', file=nextcord.File(file, file_name))
        else:
            await inter.response.send_message(f'No user entries found for wl_id {wl_id}.')


    @nextcord.slash_command()
    async def setup(self, inter):
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, setup cannot proceed.')
            return
        
        await inter.response.send_message('Setup command invoked')
      
      
    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def translation_channels(self, inter, channel_1: nextcord.TextChannel, channel_2: Optional[nextcord.TextChannel] = None, channel_3: Optional[nextcord.TextChannel] = None):
        guild_id = inter.guild.id

        # Check membership type
        membership_details = await retrieve_guild_membership(guild_id)
        if not membership_details or membership_details.get('membership_type') != 'premium':
            await inter.response.send_message('This command can only be used if the membership type is premium.')
            return

        # Ensure at least one channel is provided
        if channel_1 is None:
            await inter.response.send_message('You must provide at least one channel.')
            return

        # Call the function to add or replace translation settings
        await add_replace_translation_settings(
            guild_id,
            channel_1.id,
            channel_2.id if channel_2 else None,
            channel_3.id if channel_3 else None
        )

        # Update the channels_to_listen in the Translator cog
        translator_cog = self.bot.get_cog('Translator')
        if translator_cog:
            await translator_cog.update_channels_to_listen()

        await inter.response.send_message('Translation channels setup updated successfully.')
      

    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def verification(self, inter, verify_channel: nextcord.TextChannel, verified_role: nextcord.Role):
        guild_id = inter.guild.id
    
        # Step 1: Add verification
        response = await add_verification(guild_id, verify_channel.id, verified_role.id)
        if response is None:
            response = ''
        response += "\nVerification setup successful."
        await inter.response.send_message(response)
    
        # Step 2: Initialize verification
        captcha_cog = self.bot.get_cog("Captcha")
        if captcha_cog:
            await captcha_cog.initialize_verification(guild_id)

    
    @setup.subcommand()
    @commands.has_permissions(administrator=True)
    async def reaction_roles(self, inter, channel: nextcord.TextChannel, role_name: str, description: str, emoji: str):
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
        response = await upsert_reaction(guild_id, channel.id, emoji, description, role_id)
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
    async def welcome(self, inter, channel: nextcord.TextChannel, message: str):
        guild_id = inter.guild.id
    
        # Add or edit the welcome message
        response = await upsert_welcome_message(guild_id, channel.id, message)
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
            primary_role: nextcord.Role = nextcord.SlashOption(description="Mention the primary eligible role"),
            secondary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the secondary eligible role (optional)"),
            total_token_supply: Optional[int] = nextcord.SlashOption(description="Enter the total token supply, default TBA if left blank (optional)"),
            total_wl_spots_available: Optional[int] = nextcord.SlashOption(default=-1, description="Enter the total number of whitelist spots available (optional)"),
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
    
        # Prompt the user to upload an image
        await inter.response.send_message("Please upload an image for the token whitelist.")
    
        def check(m):
            return m.author == inter.user and m.channel == inter.channel and len(m.attachments) > 0
    
        try:
            # Await the user's response (with a timeout, say 60 seconds)
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await inter.response.send_message("Image upload timed out. Please try the command again.")
            return
    
        # Save the image to the specified directory with a unique filename
        image = message.attachments[0]
        image_path = f"media/wl_pfp/{guild_id}_{token_name}_{int(time.time())}.png"
        await image.save(image_path)
    
        # Now proceed to upsert the data to the database, including the image path
        response = await add_token_wl(
            guild_id, channel_id, blockchain, token_name, total_token_supply,
            description, primary_role_id, secondary_role_id,
            str_expiry_date, total_wl_spots_available, mint_sale_timestamp, image_path
        )
    
        # Check if the response indicates an error
        if "error" in response.lower() or "exists" in response.lower():
            await inter.followup.send("Token WL addition unsuccessful.")  # Updated this line
            return
    
        # Send success message if everything went well
        await inter.followup.send("Token whitelist entry added successfully.")  # Updated this line
    
        # Call the get_lists function from the Whitelists cog
        whitelists_cog = self.bot.get_cog("Whitelists")
        if whitelists_cog:
            await whitelists_cog.get_lists()



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
            mints_for_all_roles: str = nextcord.SlashOption(
                choices={
                    "Yes": "YES",
                    "No": "NO"
                },
                description="Select if all roles can mint"
            ),
            primary_role: nextcord.Role = nextcord.SlashOption(description="Mention the primary eligible role"),
            no_mints_primary: Optional[int] = nextcord.SlashOption(description="Enter the number of mints for primary eligible role (optional)"),
            secondary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the secondary eligible role (optional)"),
            no_mints_secondary: Optional[int] = nextcord.SlashOption(description="Enter the number of mints for secondary eligible role (optional)"),
            tertiary_role: Optional[nextcord.Role] = nextcord.SlashOption(description="Mention the tertiary eligible role (optional)"),
            no_mints_tertiary: Optional[int] = nextcord.SlashOption(description="Enter the number of mints for tertiary eligible role (optional)"),
            supply: Optional[int] = nextcord.SlashOption(description="Enter the total supply of NFTs, default TBA if left blank (optional)"),
            total_wl_spots_available: Optional[int] = nextcord.SlashOption(default=-1, description="Enter the total number of whitelist spots available (optional)"),
            mint_sale_date: Optional[str] = nextcord.SlashOption(description="Enter the launch date and time in YYYY:MM:DD HH:MM format or leave blank for TBA (optional)")
    ):
        # Convert channel and role mentions to IDs
        channel_id = str(channel_mention.id)
    
        # Use ternary operation to set -1 as default value if left blank
        no_mints_primary = no_mints_primary if no_mints_primary is not None else -1
        no_mints_secondary = no_mints_secondary if no_mints_secondary is not None else -1
        no_mints_tertiary = no_mints_tertiary if no_mints_tertiary is not None else -1
    
        primary_role_id = f'{str(primary_role.id)}:{no_mints_primary}'
        secondary_role_id = f'{str(secondary_role.id)}:{no_mints_secondary}' if secondary_role else None
        tertiary_role_id = f'{str(tertiary_role.id)}:{no_mints_tertiary}' if tertiary_role else None
    
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
    
        # Prompt the user to upload an image
        await inter.response.send_message("Please upload an image for the NFT whitelist.")
    
        def check(m):
            return m.author == inter.user and m.channel == inter.channel and len(m.attachments) > 0
    
        try:
            # Await the user's response (with a timeout, say 60 seconds)
            message = await self.bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            await inter.response.send_message("Image upload timed out. Please try the command again.")
            return
    
        # Save the image to the specified directory with a unique filename
        image = message.attachments[0]
        image_path = f"media/wl_pfp/{guild_id}_{wl_name}_{int(time.time())}.png"
        await image.save(image_path)
    
        # Now proceed to upsert the data to the database, including the image path
        response = await add_nft_wl(
            guild_id, channel_id, blockchain, wl_name, supply,
            wl_description, mints_for_all_roles, primary_role_id, secondary_role_id, tertiary_role_id,
            str_expiry_date, total_wl_spots_available, mint_sale_timestamp, image_path
        )
    
        # Check if the response indicates an error
        if "error" in response.lower() or "exists" in response.lower():
            await inter.followup.send("NFT WL addition unsuccessful.")  # Updated this line
            return
    
        # Send success message if everything went well
        await inter.followup.send("NFT whitelist entry added successfully.")  # Updated this line
    
        # Call the get_lists function from the Whitelists cog
        whitelists_cog = self.bot.get_cog("Whitelists")
        if whitelists_cog:
            await whitelists_cog.get_lists()


    @nextcord.slash_command()
    async def reset(self, inter):
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.response.send_message('Guild does not have a membership entry, reset cannot proceed.')
            return
    
        await inter.response.send_message('Reset command invoked. Use subcommands to perform specific reset operations.')

    @reset.subcommand()
    @commands.has_permissions(administrator=True)
    async def translation_settings(self, inter):
        guild_id = inter.guild.id

        # Call the function to delete translation settings
        await delete_translation_settings(guild_id)
        
        # Update the channels_to_listen in the Translator cog
        translator_cog = self.bot.get_cog('Translator')
        if translator_cog:
            await translator_cog.update_channels_to_listen()

        await inter.response.send_message('Translation settings deleted successfully.')


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


    @reset.subcommand(
        description="Delete a whitelist entry based on type."
    )
    @commands.has_permissions(administrator=True)
    async def delete_whitelist(
            self, inter,
            wl_type: str = nextcord.SlashOption(
                choices={
                    "NFT": "NFT",
                    "Token": "TOKEN"
                },
                description="Choose the type of whitelist to delete"
            )
    ):
        guild_id = str(inter.guild.id)  # Assuming you want to use the guild ID from the interaction
        
        # Call the delete_whitelist_entry function
        db_response = await delete_whitelist_entry(guild_id, wl_type)
        
        # Check for any error message in the response
        if db_response:
            await inter.response.send_message(f"An error occurred: {db_response}")
        else:
            await inter.response.send_message(f"Successfully deleted all {wl_type} whitelist entries for this guild.")


          
def setup(bot):
    bot.add_cog(Admin(bot))