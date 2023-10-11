import os
import inflect
import asyncio
from datetime import datetime
from typing import List

import nextcord
from nextcord.ext import commands

from database.database_manager import (
    retrieve_all_whitelists_for_guild,
    retrieve_whitelist_entry_by_id,
    retrieve_all_claims_for_user,
    upsert_whitelist_claim
)



class Whitelists(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.whitelists = {}  # To store the whitelists data
        self.guild_channel_ids = {}  # To store the channel IDs
        self.p = inflect.engine()  # For ordinal day formatting

    @commands.Cog.listener()
    async def on_ready(self):
        print("Whitelists ready")
        await self.get_lists()

    async def delete_existing_bot_messages(self, channel_ids):
        for channel_id in channel_ids:
            channel = self.bot.get_channel(int(channel_id))
            if channel:
                messages_to_delete = []
                async for message in channel.history(limit=100):  # Adjust the limit as needed
                    if message.author == self.bot.user:
                        messages_to_delete.append(message)

                await channel.delete_messages(messages_to_delete)
                await asyncio.sleep(1)  # Optional: add a delay to prevent rate limiting

    async def get_lists(self):
        all_channel_ids = set()  # To store unique channel IDs

        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            whitelists_data = await retrieve_all_whitelists_for_guild(guild_id)
            if whitelists_data:
                self.whitelists[guild_id] = whitelists_data
                channel_ids = [entry['channel_id'] for entry in whitelists_data]
                all_channel_ids.update(channel_ids)
                self.guild_channel_ids[guild_id] = channel_ids

        # Delete existing bot messages in all channels
        #await self.delete_existing_bot_messages(all_channel_ids)

        for guild in self.bot.guilds:
            guild_id_str = str(guild.id)
            if guild_id_str in self.whitelists:  # Check if the guild_id exists in the self.whitelists dictionary
                for entry in self.whitelists[guild_id_str]:
                    if entry['type'] == 'NFT':
                        await self.send_nft_embed(entry)
                    elif entry['type'] == 'TOKEN':
                        await self.send_token_embed(entry)


    async def send_token_embed(self, entry):
        channel_id = int(entry['channel_id'])
        channel = self.bot.get_channel(channel_id)
        if channel:
            # Check if the message with the same WL_ID already exists
            existing_message = None
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and str(entry['WL_ID']) in message.content:
                    existing_message = message
                    break
    
            if existing_message is None:
                # Extracting the roles and forming a mention string
                roles_mention = []
                for i in range(1, 3):  # Token roles are token_role_1 and token_role_2
                    role_id = entry[f'token_role_{i}']
                    if role_id:
                        roles_mention.append(f"<@&{role_id}>")
    
                roles_mention_str = '\n'.join(roles_mention)
    
                # Checking if mint_sale_date and supply are 'TBA' before attempting conversion
                formatted_date, formatted_time, formatted_supply = 'TBA', 'TBA', 'TBA'
                if entry['mint_sale_date'] != 'TBA':
                    mint_date = datetime.utcfromtimestamp(int(entry['mint_sale_date']))
                    formatted_date = f"{self.p.ordinal(mint_date.day)} {mint_date.strftime('%B %Y')}"  # type: ignore
                    formatted_time = f"{mint_date.strftime('%H:%M')} UTC"
                
                if entry['supply'] is not None:
                    formatted_supply = entry['supply']
                
                # Determine the display text for total_wl_spots
                total_wl_spots_text = "undeclared" if entry['total_wl_spots'] == -1 else entry['total_wl_spots']
                
                # Creating the embed
                title = f"**{entry['wl_name']}**"
                description = (
                    f"*{entry['wl_description']}*\n"
                    f"```\n"
                    f"Blockchain:       {entry['blockchain']}\n"
                    f"\n"
                    f"Supply:           {formatted_supply}\n"
                    f"No. spots avail:  {total_wl_spots_text}\n"
                    f"\n"
                    f"Launch date:      {formatted_date}\n"
                    f"Launch time:      {formatted_time}\n"
                    f"\n"
                    f"```"
                )
                embed = nextcord.Embed(
                    title=title,
                    description=description,
                    color=nextcord.Color.blue()  # Changed color to blue for differentiation
                )

            
                # Create a File object for the image
                image_path = entry['WL_image']
                file_extension = os.path.splitext(image_path)[1]  # Extract file extension
                file = nextcord.File(image_path, filename=f'TOKEN_WL_embed{file_extension}')
            
                # Set the image as the main image in the embed
                embed.set_image(url=f"attachment://TOKEN_WL_embed{file_extension}")

                # Set the footer and its icon in the embed
                embed.set_footer(text="https://www.SShift.xyz", icon_url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")
            
                # Sending the message, image, embed without the view and button
                message_content = (
                    f"**A token whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\n"
                    f"🚨 Use the command **/claim** and input whitelist ID: **{entry['WL_ID']}** to lock in your spot 🚨\n\n"
                    f"You have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!\n\n"
                )
                await channel.send(content=message_content, embed=embed, file=file)


    async def send_nft_embed(self, entry):
        channel_id = int(entry['channel_id'])
        channel = self.bot.get_channel(channel_id)
        if channel:
            # Check if the message with the same WL_ID already exists
            existing_message = None
            async for message in channel.history(limit=10):
                if message.author == self.bot.user and str(entry['WL_ID']) in message.content:
                    existing_message = message
                    break

            if existing_message is None:
                # Extracting the roles and forming a mention string
                roles_mention = []
                for i in range(1, 4):
                    role_data = entry[f'nft_role_mint_{i}']
                    if role_data:
                        role_id, no_mints = role_data.split(':')
                        no_mints = f"{no_mints} mints" if no_mints != '-1' else 'Unlimited'
                        roles_mention.append(f"<@&{role_id}> = {no_mints}")

                roles_mention_str = '\n'.join(roles_mention)

                # Checking if mint_sale_date and supply are 'TBA' before attempting conversion
                formatted_date, formatted_time, formatted_supply = 'TBA', 'TBA', 'TBA'
                if entry['mint_sale_date'] != 'TBA':
                    mint_date = datetime.utcfromtimestamp(int(entry['mint_sale_date']))
                    formatted_date = f"{self.p.ordinal(mint_date.day)} {mint_date.strftime('%B %Y')}"  # type: ignore
                    formatted_time = f"{mint_date.strftime('%H:%M')} UTC"
                
                if entry['supply'] is not None:
                    formatted_supply = entry['supply']
                
                # Determine the extra line based on the 'claim_all_roles' value
                if entry['claim_all_roles'] == 'YES':
                    extra_line = "For this whitelist your roles can be stacked (mints for each role)"
                else:  # Assuming 'NO' is the only other value
                    extra_line = "For this whitelist you will be assigned mints for the highest qualifying role you have (mints for one role)"
                
                # Determine the display text for total_wl_spots
                total_wl_spots_text = "undeclared" if entry['total_wl_spots'] == -1 else entry['total_wl_spots']
                
                # Creating the embed
                title = f"**{entry['wl_name']}**"
                description = (
                    f"*{entry['wl_description']}*\n"
                    f"```\n"
                    f"Blockchain:       {entry['blockchain']}\n"
                    f"\n"
                    f"Supply:           {formatted_supply}\n"
                    f"No. spots avail:  {total_wl_spots_text}\n"
                    f"\n"
                    f"Mint date:        {formatted_date}\n"
                    f"Mint time:        {formatted_time}\n"
                    f" \n"
                    f"```"
                )
                embed = nextcord.Embed(
                    title=title,
                    description=description,
                    color=nextcord.Color.gold()
                )

            
                # Create a File object for the image
                image_path = entry['WL_image']
                file_extension = os.path.splitext(image_path)[1]  # Extract file extension
                file = nextcord.File(image_path, filename=f'NFT_WL_embed{file_extension}')
            
                # Set the image as the main image in the embed
                embed.set_image(url=f"attachment://NFT_WL_embed{file_extension}")

                # Set the footer and its icon in the embed
                embed.set_footer(text="https://www.SShift.xyz", icon_url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")
            
                # Sending the message, image, embed without the view and button
                message_content = (
                    f"**An NFT whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\n"
                    f"🚨 Use the command **/claim** and input whitelist ID: **{entry['WL_ID']}** to lock in your spot 🚨\n\n"
                    f"You have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!\n\n"
                    f"{extra_line}\n\n"
                )
                await channel.send(content=message_content, embed=embed, file=file)


    @nextcord.slash_command(description="Claim your whitelist spot. (Under development)")
    async def claim(
        self, 
        interaction: nextcord.Interaction, 
        whitelist_id: str, 
        wallet_address: str
    ):
        # Check if the command is invoked within a guild
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
    
        # Get the channel IDs for the current guild from self.guild_channel_ids
        guild_id = str(interaction.guild.id)
        allowed_channels = self.guild_channel_ids.get(guild_id, [])
        
        # Convert to integers if they are not already
        allowed_channels = [int(ch) for ch in allowed_channels]

        print(f"Allowed channels: {allowed_channels}")  # Debugging line
        print(f"Interaction channel ID: {interaction.channel.id}")  # Debugging line
    
        # Check if the command is used in one of the allowed channels
        if interaction.channel and interaction.channel.id in allowed_channels:
            # Step 0: Retrieve the WL_ID from the database
            whitelist_data = await retrieve_whitelist_entry_by_id(guild_id, whitelist_id)
            if not whitelist_data:
                await interaction.response.send_message("Invalid whitelist ID.", ephemeral=True)
                return
    
            # Step 1: Check if the current timestamp is greater than expiry_date
            current_timestamp = int(datetime.utcnow().timestamp())
            if current_timestamp > int(whitelist_data['expiry_date']):
                await interaction.response.send_message("This whitelist has expired.", ephemeral=True)
                return
    
            # Ensure interaction.user and interaction.guild are not None
            if interaction.user and interaction.guild:
                member = await interaction.guild.fetch_member(interaction.user.id)
            else:
                await interaction.response.send_message("Unable to fetch user or guild information.", ephemeral=True)
                return
            
            # Step 2: Check if the user has any of the eligible roles
            wl_type = whitelist_data["type"]
            eligible_roles = []
            if wl_type == "NFT":
                eligible_roles = [whitelist_data[f'nft_role_mint_{i}'].split(':')[0] for i in range(1, 4) if whitelist_data.get(f'nft_role_mint_{i}')]
            elif wl_type == "TOKEN":
                eligible_roles = [whitelist_data[f'token_role_{i}'] for i in range(1, 3) if whitelist_data.get(f'token_role_{i}')]
    
            user_roles = [str(role.id) for role in member.roles if str(role.id) in eligible_roles]
            if not user_roles:
                await interaction.response.send_message("You do not have the required role(s) to claim this whitelist.", ephemeral=True)
                return
    
            # Step 2.5: Check if type is NFT or Token
            no_mints = -1  # Default for Token type
            if wl_type == "NFT":
                # Step 3: Check if the the WL field claim_all_roles is YES or NO
                claim_all_roles = whitelist_data['claim_all_roles'] == 'YES'
                
                # Step 4: Calculate the number of mints the user can claim
                if claim_all_roles:
                    no_mints = sum([int(whitelist_data[f'nft_role_mint_{eligible_roles.index(role) + 1}'].split(':')[1]) for role in user_roles if int(whitelist_data[f'nft_role_mint_{eligible_roles.index(role) + 1}'].split(':')[1]) != -1])
                else:
                    # Define a role rank mapping based on role IDs
                    role_ranks = {
                        whitelist_data['nft_role_mint_1'].split(':')[0]: 3,  # Primary
                        whitelist_data['nft_role_mint_2'].split(':')[0]: 2,  # Secondary
                        whitelist_data['nft_role_mint_3'].split(':')[0]: 1   # Tertiary
                    }
                    
                    # Determine the highest rank role the user has
                    highest_rank_role_id = max(user_roles, key=lambda r: role_ranks.get(r, 0))
                    no_mints = int(whitelist_data[f'nft_role_mint_{eligible_roles.index(highest_rank_role_id) + 1}'].split(':')[1])
    
            # Step 5: Use the database function to record the claim in the database
            user_roles_str = ":".join(user_roles)
            await upsert_whitelist_claim(
                whitelist_data['WL_ID'],
                guild_id,
                str(interaction.user.id),
                user_roles_str,
                wallet_address,
                no_mints
            )
    
            # Step 7: Send an ephemeral confirmation message detailing the WL_Name claimed, the address and if it’s an NFT whitelist also the number of mints allowed.
            mints_msg = f" with {no_mints} mints" if wl_type == "NFT" else ""
            await interaction.response.send_message(
                f"You have successfully claimed your spot in\n"
                f"**{whitelist_data['wl_name']}** whitelist with address:\n {wallet_address}{mints_msg}",
                ephemeral=True
            )

        else:
            await interaction.response.send_message("You can't use this command in this channel.", ephemeral=True)

    @nextcord.slash_command(description="View all your whitelists.")
    async def view_my_whitelists(
        self, 
        interaction: nextcord.Interaction
    ):
        # User Identification
        user_id = interaction.user.id
        
        # Database Query to get all claims for the user
        claims = await retrieve_all_claims_for_user(user_id)
        if not claims:
            await interaction.response.send_message("You have no whitelist claims.", ephemeral=True)
            return
    
        # Now iterate through each claim, and fetch the detailed whitelist record
        detailed_claims = []
        for claim in claims:
            guild_id = claim['guild_id']
            wl_id = claim['WL_ID']
            whitelist_detail = await retrieve_whitelist_entry_by_id(guild_id, wl_id)
            if whitelist_detail:
                detailed_claims.append((claim, whitelist_detail))
            else:
                print(f"Failed to retrieve whitelist detail for WL_ID: {wl_id} in guild: {guild_id}")
    
        # Now format and send the detailed claims data back to the user
        detailed_claims_text = "\n\n".join(
            f"Server: {self.bot.get_guild(int(claim['guild_id'])).name}\n"
            f"Type: {whitelist_detail['type']}\n"
            f"Whitelist Name: {whitelist_detail['wl_name']}\n"
            f"Blockchain: {whitelist_detail['blockchain']}\n"
            f"Supply: {format(int(whitelist_detail['supply']), ',') if whitelist_detail['supply'] != 'TBA' else whitelist_detail['supply']}\n"
            + (f"No. of Mints: {claim['no_mints']}\n" if whitelist_detail['type'] == 'NFT' else '')
            + f"Address: {claim['address'][:6]}...\n"
            + (f"Mint Date: {datetime.utcfromtimestamp(int(whitelist_detail['mint_sale_date'])).strftime('%dth %b %Y')}\nMint Time: {datetime.utcfromtimestamp(int(whitelist_detail['mint_sale_date'])).strftime('%H:%M')}\n" if whitelist_detail['type'] == 'NFT' and whitelist_detail['mint_sale_date'] != 'TBA' else '')
            + (f"Launch Date: {datetime.utcfromtimestamp(int(whitelist_detail['mint_sale_date'])).strftime('%dth %b %Y')}\nLaunch Time: {datetime.utcfromtimestamp(int(whitelist_detail['mint_sale_date'])).strftime('%H:%M')}\n" if whitelist_detail['type'] == 'TOKEN' and whitelist_detail['mint_sale_date'] != 'TBA' else '')
            for claim, whitelist_detail in detailed_claims
        )
        
        await interaction.response.send_message(detailed_claims_text, ephemeral=True)


def setup(bot):
    bot.add_cog(Whitelists(bot))