import logging
import os
import asyncio
import random
import string
from typing import Optional

import nextcord
from captcha.image import ImageCaptcha
from nextcord import Message
from nextcord.ext import commands
from nextcord.ui import Button, View

from database.database_manager import retrieve_verification, retrieve_guild_membership


class CaptchaButton(Button):
    def __init__(self, label, custom_id, row=None):
        super().__init__(style=nextcord.ButtonStyle.secondary, label=label, custom_id=custom_id)
        self.row = row


class GetRoleView(View):
    def __init__(self, member_id, role_id, thread):
        super().__init__()
        self.member_id = member_id
        self.role_id = role_id
        self.thread = thread

    @nextcord.ui.button(label="Get Role", style=nextcord.ButtonStyle.success)
    async def get_role(self, _: nextcord.ui.Button, interaction: nextcord.Interaction):
        if interaction.guild and interaction.user and interaction.user.id == self.member_id:
            verified_role = interaction.guild.get_role(self.role_id) if interaction.guild else None
            member = interaction.guild.get_member(interaction.user.id) if interaction.guild and interaction.user else None
            if verified_role and member:
                await member.add_roles(verified_role)
                await interaction.response.send_message("Role assigned successfully!")
                await self.thread.delete()  # Removed the 'reason' argument
                logging.info('Role assigned and thread deleted')
            else:
                if not verified_role:
                    await interaction.response.send_message("Error: Role could not be found.")
                    logging.warning('Role not found')
                if not member:
                    await interaction.response.send_message("Error: Member could not be found.")
                    logging.warning('Member not found')


class CaptchaView(View):
    def __init__(self, member_id, captcha_code):
        super().__init__()
        self.member_id = member_id
        self.captcha_code = captcha_code
        self.user_input = ""
        self.embed_message: Optional[Message] = None  
        self.image_url = f'attachment://captcha_{member_id}.png' 

        buttons = [
            (0, '0'), (0, '1'), (0, '2'), (0, '3'), (0, '4'),
            (1, '5'), (1, '6'), (1, '7'), (1, '8'), (1, '9')
        ]

        for row, label in buttons:
            button = CaptchaButton(label=label, custom_id=f'captcha_{label}', row=row)
            button.callback = self.add_digit_to_input
            self.add_item(button)

        delete_button = CaptchaButton(label='⏪ - DELETE', custom_id='captcha_delete', row=2)
        delete_button.callback = self.delete_last_digit
        self.add_item(delete_button)

        regenerate_button = CaptchaButton(label='New Captcha', custom_id='captcha_regenerate', row=2)
        regenerate_button.callback = self.regenerate_captcha
        self.add_item(regenerate_button)

        logging.info('CaptchaView initialized')
      

    async def add_digit_to_input(self, interaction):
        if interaction.user.id == self.member_id:
            self.user_input += interaction.data['custom_id'].split('_')[1]
    
            if self.embed_message:
                embed = self.embed_message.embeds[0]
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {self.user_input.ljust(5, '_')}"
                embed.set_image(url=self.image_url)  
                await self.embed_message.edit(embed=embed)
    
            logging.info(f"Digit added to input: {interaction.data['custom_id'].split('_')[1]}")
    
            if len(self.user_input) == 5:
                verification_settings = await retrieve_verification(interaction.guild.id)
                if verification_settings is None:
                    await interaction.channel.send("Verification settings not found.")
                    logging.warning('Verification settings not found')
                    return
    
                verified_role_id = int(verification_settings["verified_role"])
    
                if self.user_input == self.captcha_code:
                    # Get the private thread channel
                    thread = interaction.channel
    
                    # Create and send a message with the GetRoleView
                    get_role_view = GetRoleView(interaction.user.id, verified_role_id, thread)
                    await interaction.channel.send("Congratulations on successfully completing the captcha! Please click the button below to receive your role.", view=get_role_view)
                    logging.info('Verification successful, awaiting role assignment')
                else:
                    await interaction.channel.send("Verification failed. Please try again.")
                    logging.warning('Verification failed')
                    self.user_input = ""
                    
                    # Call regenerate_captcha to refresh the captcha image
                    await self.regenerate_captcha(interaction)


    async def delete_last_digit(self, interaction):
        if interaction.user.id == self.member_id:
            self.user_input = self.user_input[:-1]

            # Update the embed to show the current input
            if self.embed_message:
                embed = self.embed_message.embeds[0]
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {self.user_input.ljust(5, '_')}"
                embed.set_image(url=self.image_url)  # Set the image URL back to its original value
                await self.embed_message.edit(embed=embed)
            
            logging.info(f"Last digit deleted, current input: {self.user_input}")

    async def regenerate_captcha(self, interaction):
        if interaction.user.id == self.member_id:
            new_captcha_code = ''.join(random.choices(string.digits, k=5))  # Generate a new captcha code
            self.captcha_code = new_captcha_code  # Update the current captcha code

            image = self.create_captcha_image(new_captcha_code)  # Create a new captcha image
            image_path = f'temp/captcha_{self.member_id}.png'
            image.save(image_path)  # Save the new image

            # Update the embed with the new image and reset the input
            if self.embed_message:
                embed = self.embed_message.embeds[0]
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {'_'*5}"
                embed.set_image(url=f'attachment://captcha_{self.member_id}.png')  # Set the image URL to the new image
                files = [nextcord.File(image_path, filename=f'captcha_{self.member_id}.png')]
                await self.embed_message.edit(files=files, embed=embed)  # Edit the message with the new embed
                
            self.user_input = ""  # Reset the user input
            logging.info('Captcha regenerated')

    def create_captcha_image(self, captcha_code):
        logging.info('Creating captcha image')
        image_captcha = ImageCaptcha(width=280, height=90)
        image = image_captcha.generate_image(captcha_code)
        return image

class Captcha(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.captchas = {}
        logging.info('Captcha cog initialized')

    @commands.Cog.listener()
    async def on_ready(self):
        print("Captcha Ready")
        # Initialization moved to a separate function

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:  # Ignore messages from bots
            return
    
        if message.guild:  # Check if the message is in a guild and not a DM
            verification_settings = await retrieve_verification(message.guild.id)
            if verification_settings:
                verify_channel_id = int(verification_settings["verify_channel"])
                if message.channel.id == verify_channel_id and message.content != "/verify":
                    await message.delete()


    async def initialize_verification(self, guild_id):
        verification_settings = await retrieve_verification(guild_id)
        if verification_settings:
            self.verify_channel_id = int(verification_settings["verify_channel"])  # Store the channel ID
            await self.send_verification_prompt(self.verify_channel_id)

    async def send_verification_prompt(self, verify_channel):
        channel = self.bot.get_channel(int(verify_channel))
        embed = nextcord.Embed(
            title=" ",
            description="**Thank you for using SShift Bot!**\n\nTo start the verification process\n\nplease type **/verify**.",
            color=0x7851A9
        )
    
        # Create a File object for the shield image
        file = nextcord.File("media/shield.png", filename="shield.png")
    
        # Set the shield image as the main image in the embed
        embed.set_image(url="attachment://shield.png")
      
        # Set thumbnail image
        embed.set_thumbnail(url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")

        # Set the footer and its icon in the embed
        embed.set_footer(text="https://www.sshift.xyz", icon_url="https://gn3l76apsy7n5ntu2vde6vqhblsseufejityx5zyxoronukmmhrq.arweave.net/M3a_-A-WPt62dNVGT1YHCuUiUKRKJ4v3OLui5tFMYeM/16.gif")
        
        await channel.send(file=file, embed=embed)


    @nextcord.slash_command()
    async def verify(self, inter):
        logging.info(f'Verification initiated by: {inter.user.id}')
    
        verification_settings = await retrieve_verification(inter.guild.id)
        if verification_settings is None:
            logging.warning('Verification settings not found')
            await inter.response.send_message('Verification settings not found.')
            return
        
        # Check if the user already has the verified role
        verified_role_id = int(verification_settings["verified_role"])
        member = inter.guild.get_member(inter.user.id)
        if verified_role_id in [role.id for role in member.roles]:
            await inter.response.send_message('You are already verified.', ephemeral=True)
            return
    
        # Create a private thread with the user's display name
        thread = await inter.channel.create_thread(name=f"Verification-{inter.user.display_name}", type=nextcord.ChannelType.private_thread)
        
        # Mention the user in the private thread, prompting them to complete the verification
        await thread.send(f"{inter.user.mention}, please complete the verification process below:")
        
        # Call send_captcha with the thread as an additional argument
        captcha_cog = self.bot.get_cog("Captcha")
        if captcha_cog:
            await captcha_cog.send_captcha(inter.user, thread)


    async def send_captcha(self, member, thread):
        logging.info('Sending captcha')
        
        # Using the thread parameter as the channel
        channel = thread
    
        if not channel:
            logging.warning('Verification channel not found')
            return
    
        captcha_code = self.generate_captcha_code()
        image = self.create_captcha_image(captcha_code)
        
        if not os.path.exists('temp'):
            os.makedirs('temp')
    
        image_path = f'temp/captcha_{member.id}.png'
        image.save(image_path)
        
        self.captchas[member.id] = captcha_code
    
        embed = nextcord.Embed(title="CAPTCHA Verification", description=f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {'_'*5}")
        files = [nextcord.File(image_path, filename=f'captcha_{member.id}.png')]
        embed.set_image(url=f'attachment://captcha_{member.id}.png')
        
        view = CaptchaView(member.id, captcha_code)
        
        message = await channel.send(files=files, embed=embed, view=view)
        view.embed_message = message
        logging.info('Captcha sent')

    def generate_captcha_code(self):
        logging.info('Generating captcha code')
        return ''.join(random.choices(string.digits, k=5))

    def create_captcha_image(self, captcha_code):
        logging.info('Creating captcha image')
        image_captcha = ImageCaptcha(width=280, height=90)
        image = image_captcha.generate_image(captcha_code)
        return image

def setup(bot):
    bot.add_cog(Captcha(bot))
    logging.info("Captcha cog loaded")