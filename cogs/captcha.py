import logging
import os
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

                verified_role = interaction.guild.get_role(int(verification_settings["verified_role"]))

                if self.user_input == self.captcha_code:
                    if verified_role:
                        await interaction.user.add_roles(verified_role)
                        await interaction.channel.send("Verification successful!")
                        logging.info('Verification successful')
                    else:
                        await interaction.channel.send("Verification successful, but the role could not be assigned.")
                        logging.warning('Verification successful, but the role could not be assigned')
                else:
                    await interaction.channel.send("Verification failed. Please try again.")
                    logging.warning('Verification failed')
                    self.user_input = ""

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

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.data['custom_id'] == "start_verification":
            await interaction.response.defer()  # Adding this line to defer the response
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
    
            channel = self.bot.get_channel(int(verification_settings["verify_channel"]))
            if channel:
                await channel.send(f"Welcome to {interaction.guild.name}, please verify to enter {interaction.user.mention}")
            await self.send_captcha(interaction.user, verification_settings)

    @nextcord.slash_command()
    async def verify(self, inter):
        logging.info('Verify command invoked')
        await inter.response.defer()
        
        verification_settings = await retrieve_verification(inter.guild.id)
        if verification_settings is None:
            await inter.followup.send("Verification settings not found.")
            logging.warning('Verification settings not found')
            return
        
        if str(inter.channel.id) != verification_settings["verify_channel"]:
            await inter.followup.send("This command can only be used in the verification channel.")
            logging.warning('Verify command used in the wrong channel')
            return
    
        guild_membership = await retrieve_guild_membership(inter.guild.id)
        if guild_membership is None:
            await inter.followup.send('Guild is not a member, verification inactive.')
            logging.warning('Guild is not a member, verification inactive.')
            return
        
        await self.send_captcha(inter.user, verification_settings)
        await inter.followup.send(f"{inter.user.mention}, please verify using the captcha.")

    async def send_captcha(self, member, verification_settings):
        logging.info('Sending captcha')
        
        channel = self.bot.get_channel(int(verification_settings["verify_channel"]))
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