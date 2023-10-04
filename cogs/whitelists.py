import inflect
from datetime import datetime

import nextcord
from nextcord.ext import commands

from database.database_manager import retrieve_all_whitelists_for_guild


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

  
    async def get_lists(self):
        for guild in self.bot.guilds:
            guild_id = str(guild.id)
            whitelists_data = await retrieve_all_whitelists_for_guild(guild_id)
            if whitelists_data:
                self.whitelists[guild_id] = whitelists_data
                self.guild_channel_ids[guild_id] = [entry['channel_id'] for entry in whitelists_data]
                for entry in whitelists_data:
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
                f"Use the command **/claim** to submit your wallet and lock in your spot 🔥🐸🔥"
            )
            embed = nextcord.Embed(
                title=title,
                description=description,
                color=nextcord.Color.yellow()
            )

            # Sending the message, image, and embed
            message_content = f"**An NFT whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\nYou have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!\n\n{extra_line}"
            image_path = 'media/NFT_WL_embed.jpg'
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
                f"Use the command **/claim** to submit your wallet and lock in your spot 🔥🐸🔥"
            )
            embed = nextcord.Embed(
                title=title,
                description=description,
                color=nextcord.Color.blue()  # Changed color to blue for differentiation
            )

            # Sending the message, image, and embed
            message_content = f"**A token whitelist brought to you by SShift Bot for:**\n\n{roles_mention_str}\n\nYou have till until <t:{int(entry['expiry_date'])}:F> to claim and submit your wallet!"
            image_path = 'media/NFT_WL_embed.jpg'
            file = nextcord.File(image_path, filename='NFT_WL_embed.jpg')
            await channel.send(content=message_content, embed=embed, file=file)



def setup(bot):
    bot.add_cog(Whitelists(bot))
