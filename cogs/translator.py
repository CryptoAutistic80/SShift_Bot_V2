import nextcord
from nextcord.ext import commands
from langdetect import detect, LangDetectException
from database.database_manager import retrieve_translation_settings, insert_translation, retrieve_translation
from main import GPT_MODEL
import openai

def should_translate(message):
    if message.content.startswith(('!', '/')):
        return False
    if message.reference:
        return False
    if len(message.content.split()) < 4:
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
            should_translate(message)):
            
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
                    model=GPT_MODEL,
                    messages=chat_message,
                    temperature=0.2,
                    max_tokens=500,
                    frequency_penalty=0.0
                )
                translation = response['choices'][0]['message']['content'].strip()
                await insert_translation(guild_id, translation, str(message.id))  # Insert translation into the database
    
                await message.add_reaction('🌎')  # React with a globe emoji after translation has been inserted

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
                     await ctx.send(f'Translation: {translation}', delete_after=15)  # The message will self-delete after 15 seconds
                 else:
                     await ctx.send(f"No translation found for message ID {original_message_id}", delete_after=15)  # The message will self-delete after 15 seconds
             else:
                 await ctx.send("Please reply to a message to view its translation.", delete_after=15)  # The message will self-delete after 15 seconds
         except Exception as e:
             await ctx.send("An error occurred. Please try again later.", delete_after=15)  # The message will self-delete after 15 seconds


    @nextcord.slash_command(name="reply", description="Reply to a user's last message.")
    async def reply(self, interaction: nextcord.Interaction, user: nextcord.Member, text: str):
        try:
            await interaction.response.defer()  # Defer the initial response
    
            # Ensure the command is used in a TextChannel
            if isinstance(interaction.channel, nextcord.TextChannel):
                messages = await interaction.channel.history(limit=50).flatten()
                user_message = None
                for msg in messages:
                    if msg.author == user:
                        user_message = msg
                        break
    
                if not user_message:
                    await interaction.followup.send("Couldn't find a recent message from the selected user.")
                    return
    
                original_content = user_message.content
                system_prompt = (
                    "Translate the reply to match the language and style of the original message."
                )
                chat_message = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Original message: '{original_content}'. Reply: '{text}'."}
                ]
    
                response = openai.ChatCompletion.create(
                    model=GPT_MODEL,
                    messages=chat_message,
                    temperature=0.2,
                    max_tokens=500,
                    frequency_penalty=0.0
                )
                translation = response['choices'][0]['message']['content'].strip()
    
                if interaction.user is not None:
                    response_message = f"{interaction.user.mention} replied:\n\n**Original:** {text}\n\n**Translation:** {translation}"
                    await interaction.followup.send(response_message)  # Use followup.send to send the final response
                else:
                    await interaction.followup.send("An error occurred while processing your request.")
    
            else:
                await interaction.followup.send("This command can only be used in text channels.")
                return
    
        except Exception as e:
            print(f"Error executing /reply command: {e}")
            await interaction.followup.send("An error occurred while processing your request.")


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
                    model=GPT_MODEL,
                    messages=chat_message,
                    temperature=0.2,
                    max_tokens=500,
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
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == '🌎' and not user.bot:
            # Assume the reaction is on a message in a TextChannel
            message = reaction.message
            guild_id = message.guild.id
            original_message_id = message.id

            # Fetch the translation from the database
            translation = await retrieve_translation(guild_id, str(original_message_id))

            if translation:
                # Send the translation as a message
                await message.channel.send(
                    f'Translation: {translation}',
                    delete_after=15  # The message will self-delete after 15 seconds
                )

                # Remove the user's reaction
                await reaction.remove(user)
            else:
                print(f"No translation found for message ID {original_message_id}")


def setup(client):
    client.add_cog(Translator(client))