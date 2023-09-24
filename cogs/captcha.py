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
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {self.user_input.ljust(8, '_')}"
                embed.set_image(url=self.image_url)  
                await self.embed_message.edit(embed=embed)
    
            logging.info(f"Digit added to input: {interaction.data['custom_id'].split('_')[1]}")
    
            if len(self.user_input) == 8:
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
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {self.user_input.ljust(8, '_')}"
                embed.set_image(url=self.image_url)  # Set the image URL back to its original value
                await self.embed_message.edit(embed=embed)
            
            logging.info(f"Last digit deleted, current input: {self.user_input}")

    async def regenerate_captcha(self, interaction):
        if interaction.user.id == self.member_id:
            new_captcha_code = ''.join(random.choices(string.digits, k=8))  # Generate a new captcha code
            self.captcha_code = new_captcha_code  # Update the current captcha code

            image = self.create_captcha_image(new_captcha_code)  # Create a new captcha image
            image_path = f'temp/captcha_{self.member_id}.png'
            image.save(image_path)  # Save the new image

            # Update the embed with the new image and reset the input
            if self.embed_message:
                embed = self.embed_message.embeds[0]
                embed.description = f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {'_'*8}"
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

    async def send_verification_prompt(self, _, verify_channel):
        # Get the verification channel
        channel = self.bot.get_channel(int(verify_channel))
        
        # Send the message with the embed and the button
        embed = nextcord.Embed(
            title="Welcome to SShift Bot!", 
            description="Thank you for using SShift Bot! Please follow the instructions carefully to complete the verification process. We're thrilled to have you here!", 
            color=0x00ff00
        )
        view = nextcord.ui.View()
        view.add_item(nextcord.ui.Button(label="Start Verification", custom_id="start_verification", style=nextcord.ButtonStyle.primary))
        await channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        # Check if 'custom_id' is in interaction.data to prevent KeyError
        if 'custom_id' in interaction.data and interaction.data['custom_id'] == "start_verification":
            logging.info(f'Interaction received by user {interaction.user.id}')
            
            # Check if the interaction has not been acknowledged yet to prevent HTTPException
            try:
                await interaction.response.defer()
                logging.info(f'Interaction deferred by user {interaction.user.id}')
            except nextcord.errors.HTTPException as e:
                if "Interaction has already been acknowledged" in str(e):
                    logging.warning(f'Interaction already acknowledged by user {interaction.user.id}')
                else:
                    logging.error(f'An unexpected HTTPException occurred: {e}')
                return
    
            logging.info(f'Start verification initiated by: {interaction.user.id}')
    
            guild_membership = await retrieve_guild_membership(interaction.guild.id)
            if guild_membership is None:
                logging.warning('Guild does not have a membership entry, setup cannot proceed.')
                await interaction.followup.send('Guild does not have a membership entry, setup cannot proceed.')  # Changed to followup.send
                return
    
            verification_settings = await retrieve_verification(interaction.guild.id)
            if verification_settings is None:
                logging.warning('Verification settings not found')
                await interaction.followup.send('Verification settings not found.')  # Changed to followup.send
                return
            
            # Check if the user already has the verified role
            verified_role_id = int(verification_settings["verified_role"])  # Casting to int
            member = interaction.guild.get_member(interaction.user.id)
            if verified_role_id in [role.id for role in member.roles]:
                await interaction.followup.send('You are already verified.', ephemeral=True)
                return

            # Create a private thread with the user's display name
            thread = await interaction.channel.create_thread(name=f"Verification-{interaction.user.display_name}", type=nextcord.ChannelType.private_thread)
            
            # Mention the user in the private thread, prompting them to complete the verification
            await thread.send(f"{interaction.user.mention}, please complete the verification process below:")
        
            # Sending an ephemeral message in the channel inviting the user to the private thread
            await interaction.followup.send(f'Please go to {thread.mention} to complete your verification.', ephemeral=True)
            
            # Call send_captcha with the thread as an additional argument
            await self.send_captcha(interaction.user, thread)


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
    
        embed = nextcord.Embed(title="CAPTCHA Verification", description=f"Hey there froggies 🐸! Just a quick hop, skip, and a jump through this CAPTCHA to prove you're more amphibian than bot - remember, the only bot allowed here is me! Happy trading! 🚀📈.\n\nCurrent Input: {'_'*8}")
        files = [nextcord.File(image_path, filename=f'captcha_{member.id}.png')]
        embed.set_image(url=f'attachment://captcha_{member.id}.png')
        
        view = CaptchaView(member.id, captcha_code)
        
        message = await channel.send(files=files, embed=embed, view=view)
        view.embed_message = message
        logging.info('Captcha sent')

    def generate_captcha_code(self):
        logging.info('Generating captcha code')
        return ''.join(random.choices(string.digits, k=8))

    def create_captcha_image(self, captcha_code):
        logging.info('Creating captcha image')
        image_captcha = ImageCaptcha(width=280, height=90)
        image = image_captcha.generate_image(captcha_code)
        return image

def setup(bot):
    bot.add_cog(Captcha(bot))
    logging.info("Captcha cog loaded")