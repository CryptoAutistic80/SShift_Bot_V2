import inflect
import asyncio
from datetime import datetime
from typing import List

import nextcord
from nextcord.ext import commands

from database.database_manager import retrieve_all_whitelists_for_guild, retrieve_whitelist_entry_by_id, retrieve_all_claims_for_user, upsert_whitelist_claim



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
        await self.delete_existing_bot_messages(all_channel_ids)

        for guild in self.bot.guilds:
            guild_id_str = str(guild.id)
            if guild_id_str in self.whitelists:  # Check if the guild_id exists in the self.whitelists dictionary
                for entry in self.whitelists[guild_id_str]:
                    if entry['type'] == 'NFT':
                        await self.send_nft_embed(entry)
                    elif entry['type'] == 'TOKEN':
                        await self.send_token_embed(entry)


    async def send_nft_embed(self, entry):
        channel_id = int(entry['channel_id'])
        channel = self.bot.get_channel(channel_id)
        if channel:
            # Extracting the roles and forming a mention string
            roles_mention = []
            for i in range(1, 4):
                role_data = entry[f'nft_role_mint_{i}']
                if role_data:
                    role_id, no_mints = role_data.split(':')
                    no_mints = f"{no_mints} mints" if no_mints != '-1' else 'Unlimited'
                    roles_mention.append(f"<@&{role_id}> = {no_mints}")

            roles_mention_str = '\n'.join(roles_mention)

            # Formatting the date
            mint_date = datetime.utcfromtimestamp(int(entry['mint_sale_date']))
            formatted_date = f"{self.p.ordinal(mint_date.day)} {mint_date.strftime('%B %Y')} at {mint_date.strftime('%H:%M')} UTC"  # type: ignore

            # Determine the extra line based on the 'claim_all_roles' value
            if entry['claim_all_roles'] == 'YES':
                extra_line = "For this whitelist your roles can be stacked (mints for each role)"
            else:  # Assuming 'NO' is the only other value
                extra_line = "For this whitelist you will be assigned mints for the highest qualifying role you have (mints for one role)"

            # Creating the embed
            title = f"**{entry['wl_name']}**"
            description = (
                f"{entry['wl_description']}\n"
                f"```\n"
                f"Blockchain:                {entry['blockchain']}\n"
                f"Supply:                    {entry['supply']}\n"
                f"Total spots available:     {entry['total_wl_spots']}\n"  # New line for total whitelist spots
                f"Mint Date:                 {formatted_date}\n"
                f"```"
                f" \n"
            )
            embed = nextcord.Embed(
                title=title,
                description=description,
                color=nextcord.Color.yellow()
            )

            # Sending the message, image, embed without the view and button
            message_content = (
                f"**An NFT whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\n"
                f"🚨 Use the command **/claim** and input whitelist ID: **{entry['WL_ID']}** to lock in your spot 🚨\n\n"
                f"You have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!\n\n"
                f"{extra_line}\n\n"
            )
            image_path = 'media/NFT_WL_embed.webp'
            file = nextcord.File(image_path, filename='NFT_WL_embed.jpg')
            await channel.send(content=message_content, embed=embed, file=file)



    async def send_token_embed(self, entry):
        channel_id = int(entry['channel_id'])
        channel = self.bot.get_channel(channel_id)
        if channel:
            # Extracting the roles and forming a mention string
            roles_mention = []
            for i in range(1, 3):  # Token roles are token_role_1 and token_role_2
                role_id = entry[f'token_role_{i}']
                if role_id:
                    roles_mention.append(f"<@&{role_id}>")

            roles_mention_str = '\n'.join(roles_mention)

            # Formatting the date
            mint_date = datetime.utcfromtimestamp(int(entry['mint_sale_date']))
            formatted_date = f"{self.p.ordinal(mint_date.day)} {mint_date.strftime('%B %Y')} at {mint_date.strftime('%H:%M')} UTC"  # type: ignore

            # Creating the embed
            title = f"**{entry['wl_name']}**"
            description = (
                f"{entry['wl_description']}\n"
                f"```\n"
                f"Blockchain:                {entry['blockchain']}\n"
                f"Supply:                    {entry['supply']}\n"
                f"Total spots available:     {entry['total_wl_spots']}\n"
                f"Launch Date:               {formatted_date}\n"
                f"```"
                f" \n"
            )
            embed = nextcord.Embed(
                title=title,
                description=description,
                color=nextcord.Color.blue()  # Changed color to blue for differentiation
            )

            # Sending the message, image, embed without the view and button
            message_content = (
                f"**A token whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\n"
                f"🚨 Use the command **/claim** and input whitelist ID: **{entry['WL_ID']}** to lock in your spot 🚨\n\n"
                f"You have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!\n\n"
            )
            image_path = 'media/TOKEN_WL_embed.webp'
            file = nextcord.File(image_path, filename='NFT_WL_embed.jpg')
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
                    primary_role = user_roles[0]
                    no_mints = int(whitelist_data[f'nft_role_mint_{eligible_roles.index(primary_role) + 1}'].split(':')[1])
    
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


def setup(bot):
    bot.add_cog(Whitelists(bot))