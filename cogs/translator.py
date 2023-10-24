import re
import logging
import nextcord
from nextcord.ext import commands
from langdetect import detect, LangDetectException
from database.database_manager import retrieve_translation_settings, insert_translation, retrieve_translation
from main import TRAN_GPT_MODEL
import openai

def preprocess_message(text):
    try:
        # Remove mentions
        cleaned_text = re.sub(r'@\\w+', '', text)
        return cleaned_text.strip()
    except Exception as e:
        logging.error(f"Error in preprocess_message: {e}")
        return text

def should_translate(message):
    text = message.content
    
    if message.reference:
        return False
    
    cleaned_text = preprocess_message(text)
    
    # Checking if cleaned_text is empty or contains specific strings
    if not cleaned_text or cleaned_text in ['!fetch', '!reply']:
        return False

    if cleaned_text.startswith('!reply '):
        return False
    
    # Check for non-Latin scripts
    non_latin_patterns = [
        r'[\u0600-ۿ]',  # Arabic
        r'[ঀ-\u09ff]',  # Bengali
        r'[一-\u9fff𠀀-\U0002a6df]',  # Chinese
        r'[Ѐ-ӿ]',  # Cyrillic
        r'[ऀ-ॿ]',  # Devanagari
        r'[Ͱ-Ͽ]',  # Greek
        r'[\u0a80-૿]',  # Gujarati
        r'[\u0a00-\u0a7f]',  # Gurmukhi
        r'[\u0590-\u05ff]',  # Hebrew
        r'[\u3040-ヿ㐀-\u4dbf]',  # Japanese
        r'[ಀ-\u0cff]',  # Kannada
        r'[가-\ud7af]',  # Korean
        r'[ഀ-ൿ]',  # Malayalam
        r'[\u0b00-\u0b7f]',  # Oriya (Odia)
        r'[\u0d80-\u0dff]',  # Sinhala
        r'[\u0b80-\u0bff]',  # Tamil
        r'[ఀ-౿]',  # Telugu
        r'[\u0e00-\u0e7f]',  # Thai
        r'[ༀ-\u0fff]',   # Tibetan
        r'[\u1400-\u167F]'  # Inuktitut
    ]
    for pattern in non_latin_patterns:
        if re.search(pattern, cleaned_text):
            return True
    
    if len(cleaned_text.split()) < 4:
        return False

    return True

def detect_language(text):
    try:
        lang = detect(text)
        return lang
    except LangDetectException:
        print("Could not determine the language.")
        return None
    except Exception as e:  # Catch any other exceptions
        print(f"Unexpected error: {e}")
        return None

class Translator(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.channels_to_listen = {}  # A dictionary to store channel IDs for each guild

    async def update_channels_to_listen(self, specific_guild_id=None):
        target_guilds = self.client.guilds
        if specific_guild_id:
            guild = self.client.get_guild(specific_guild_id)
            if guild:
                target_guilds = [guild]

        # Retrieve and update channels to listen for the target guilds
        for guild in target_guilds:
            translation_settings = await retrieve_translation_settings(guild.id)
            if translation_settings:
                channel_1, channel_2, channel_3, _ = translation_settings
                self.channels_to_listen[guild.id] = [ch for ch in (channel_1, channel_2, channel_3) if ch]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Translator ready")
        await self.update_channels_to_listen()  # Update the channels to listen to when the bot is ready

    @commands.Cog.listener()
    async def on_message(self, message):
        guild_id = message.guild.id
        channel_id_str = str(message.channel.id)
        
        if (not message.author.bot and 
            guild_id in self.channels_to_listen and 
            channel_id_str in self.channels_to_listen[guild_id] and 
            should_translate(message)):  # Adjusted this line to pass message object
            
            lang = detect_language(message.content)
            if lang and lang != 'en':
                # Translate non-English message to English using OpenAI
                system_prompt = (
                    "Your singular purpose is to translate any non-English language you receive into perfect English, "
                    "while ensuring you maintain and accurately represent any cultural nuances and slang expressed in the original text."
                )
                chat_message = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Translate the following to English: '{message.content}'"}
                ]
                response = openai.ChatCompletion.create(
                    model=TRAN_GPT_MODEL,
                    messages=chat_message,
                    temperature=0.2,
                    max_tokens=1000,
                    frequency_penalty=0.0
                )
                translation = response['choices'][0]['message']['content'].strip()
                await insert_translation(guild_id, translation, str(message.id))  # Insert translation into the database
    
                await message.add_reaction('🌎')

    @nextcord.message_command(name="TRANSLATION")
    async def fetch_translation(self, interaction: nextcord.Interaction, target_message: nextcord.Message):
        """Fetch the translation for a right-clicked (context menu) message"""
        try:
            original_message_id = target_message.id
            # Fetch the translation from the database
            retrieved_translation = await retrieve_translation(interaction.guild.id, str(original_message_id))

            # If a translation exists, send it
            if retrieved_translation:
                await interaction.response.send_message(retrieved_translation, ephemeral=True)
            else:
                await interaction.response.send_message(f"No translation found for message ID {original_message_id}", ephemeral=True)
        except Exception as e:
            print(f"Error executing fetch_translation message-command: {e}")
            await interaction.response.send_message("An error occurred while fetching the translation.", ephemeral=True)
          
    @commands.command(name="view", help="View the translation for a replied message")
    async def view_translation(self, ctx):
         """View the translation for a replied message using traditional command"""
  
         # Ensure the command is used in a guild
         if not ctx.guild:
             await ctx.send("This command can only be used in a guild.")
             return
  
         try:
             # Check if the context is in reply to an existing message
             if ctx.message.reference:
                 original_message_id = ctx.message.reference.message_id
  
                 # Fetch the translation from the database
                 translation = await retrieve_translation(ctx.guild.id, str(original_message_id))
  
                 # If a translation exists, send it
                 if translation:
                     await ctx.send(f'Translation: {translation}')
                 else:
                     await ctx.send(f"No translation found for message ID {original_message_id}", delete_after=2.5)  # The message will self-delete after 15 seconds
             else:
                 await ctx.send("Please reply to a message to view its translation.", delete_after=2.5)  # The message will self-delete after 15 seconds
         except Exception as e:
             await ctx.send("An error occurred. Please try again later.", delete_after=2.5)  # The message will self-delete after 15 seconds


    @commands.command(name="reply", help="Translate your reply to the language of the original message")
    async def reply_command(self, ctx, *, user_reply: str):
        # Ensure the command is used in a TextChannel
        if not isinstance(ctx.channel, nextcord.TextChannel):
            await ctx.send("This command can only be used in text channels.")
            return

        try:
            # Log the command invocation
            print(f"!reply command invoked by {ctx.author.name} ({ctx.author.id})")

            # Check if the context is in reply to an existing message
            if ctx.message.reference:
                original_message_id = ctx.message.reference.message_id
                original_message = await ctx.channel.fetch_message(original_message_id)
                original_content = original_message.content

                # Construct the prompt for OpenAI
                system_prompt = (
                    "Translate the reply to match the language and style of the original message."
                )
                chat_message = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original message: '{original_content}'. Reply: '{user_reply}'."}
                ]

                # Use OpenAI API to get the translation
                response = openai.ChatCompletion.create(
                    model=TRAN_GPT_MODEL,
                    messages=chat_message,
                    temperature=0.2,
                    max_tokens=1000,
                    frequency_penalty=0.0
                )
                translation = response['choices'][0]['message']['content'].strip()

                # Delete the user's original !reply message
                await ctx.message.delete()

                # Bot replies to the original message with the formatted translation
                formatted_translation = f"{ctx.author.mention} replied: {translation}"
                await original_message.reply(formatted_translation)

            else:
                print("The !reply command was not used in reply to a message.")
                await ctx.send("Please use the !reply command in response to an existing message.")
        except Exception as e:
            print(f"Error executing !reply command: {e}")
            await ctx.send("An error occurred. Please try again later.")


    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.emoji.name == '🌎' and not payload.member.bot:
           channel = self.client.get_channel(payload.channel_id)
           message = await channel.fetch_message(payload.message_id)
           guild_id = payload.guild_id
           original_message_id = payload.message_id

           # Fetch the translation from the database
           translation = await retrieve_translation(guild_id, str(original_message_id))

           if translation:
               # Send the translation as a message
               await channel.send(f'Translation: {translation}', delete_after=7.5)
           else:
               # Notify the user if no translation is found
               await channel.send(f"No translation found for message ID {original_message_id}", delete_after=2.5)

           # Remove the user's reaction
           await message.remove_reaction(payload.emoji, payload.member)


def setup(client):
    client.add_cog(Translator(client))