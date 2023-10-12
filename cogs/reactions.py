import logging
import nextcord
from nextcord.ext import commands
from collections import defaultdict
from database.database_manager import retrieve_reactions  # Assuming this is how you import the function

class Reactions(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.guild_reactions = {}  # To store the reactions for each guild

    @commands.Cog.listener()
    async def on_ready(self):
        print("Reactions cog ready")
        await self.load_reactions()

    async def load_reactions(self, specific_guild_id=None):
        target_guilds = self.client.guilds
        if specific_guild_id:
            guild = self.client.get_guild(specific_guild_id)
            if guild:
                target_guilds = [guild]

        # Retrieve and sort reactions for the target guilds
        for guild in target_guilds:
            reactions = await retrieve_reactions(guild.id)
            if reactions:
                sorted_reactions = defaultdict(list)
                for reaction in reactions:
                    channel_id, emoji, description, role_id = reaction
                    sorted_reactions[channel_id].append((emoji, description, role_id))
                self.guild_reactions[guild.id] = sorted_reactions

                for channel_id, role_data in sorted_reactions.items():
                    channel = guild.get_channel(int(channel_id))
                    if channel:
                        existing_message = None
                        async for message in channel.history(limit=100):  # Increase limit for better accuracy
                            if message.author == self.client.user and len(message.embeds) > 0 and message.embeds[0].title == "**React for Roles**":
                                existing_message = message
                                break

                        embed = nextcord.Embed(
                            title="**React for Roles**",
                            description="\u200b",  
                            color=0x7851A9
                        )

                        # Set the image as the main image in the embed
                        file = nextcord.File("media/reactions4.png", filename="reactions4.png")
                        embed.set_image(url="attachment://reactions4.png")

                        # Set thumbnail image
                        embed.set_thumbnail(url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")

                        # Set the footer and its icon in the embed
                        embed.set_footer(text="https://www.sshift.xyz", icon_url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")

                        for emoji, desc, role_id in role_data:
                            role = guild.get_role(int(role_id))
                            if role:
                                embed.add_field(name=f"{emoji} - @{role.name} - {desc}", value="\u200b", inline=False)

                        # If there's an existing message, edit it. Otherwise, send a new one.
                        if existing_message:
                            await existing_message.edit(embed=embed)
                            msg = existing_message
                        else:
                            msg = await channel.send(file=file, embed=embed)

                        current_reactions = [str(reaction.emoji) for reaction in msg.reactions]
                        for emoji, _, _ in role_data:
                            if emoji not in current_reactions:
                                await msg.add_reaction(emoji)

  
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Check if the user is the bot itself
        if payload.user_id == self.client.user.id:
            return
    
        if payload.guild_id in self.guild_reactions:
            channel_reactions = self.guild_reactions[payload.guild_id].get(str(payload.channel_id), [])
            for emoji, _, role_id in channel_reactions:
                if str(payload.emoji) == emoji:
                    guild = self.client.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(int(role_id))
                    if role:
                        await member.add_roles(role)
                        break


    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id in self.guild_reactions:
            channel_reactions = self.guild_reactions[payload.guild_id].get(str(payload.channel_id), [])
            for emoji, _, role_id in channel_reactions:
                if str(payload.emoji) == emoji:
                    guild = self.client.get_guild(payload.guild_id)
                    member = guild.get_member(payload.user_id)
                    role = guild.get_role(int(role_id))
                    if role:
                        await member.remove_roles(role)
                        break

def setup(client):
    client.add_cog(Reactions(client))
    logging.info("Reaction cog loaded")
