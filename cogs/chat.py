import asyncio
import logging
from collections import deque
from nextcord.ext import commands

import openai

# Assuming GPT_MODEL is imported from the main file
from main import GPT_MODEL

logger = logging.getLogger('discord')

class SimpleChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}  # A dictionary to hold conversation history by channel_id
        self.api_semaphore = asyncio.Semaphore(5)  # Limiting the API requests
        self.initial_message = {'role': 'system', 'content': 'Hello, how can I assist you today?'}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Chat loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Restrict to the specific channel ID for development purposes
        if message.channel.id != 1112510368879743146:
            return

        # Check if the bot is mentioned
        if self.bot.user in message.mentions:
            channel_id = message.channel.id

            # Initialize conversation for the channel if it doesn't exist
            if channel_id not in self.conversations:
                self.conversations[channel_id] = deque(maxlen=5)  # Limiting to the last 5 messages
                self.conversations[channel_id].append(self.initial_message)

            # Append the user's message to the conversation history
            self.conversations[channel_id].append({'role': 'user', 'content': message.content})

            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        # Make OpenAI API call to generate a message
                        response = await asyncio.to_thread(
                            openai.ChatCompletion.create,
                            model=GPT_MODEL,  # Using GPT_MODEL imported from main
                            messages=list(self.conversations[channel_id])
                        )
                        assistant_reply = response['choices'][0]['message']['content']

                        # Break down the reply into chunks of 2000 characters each
                        reply_chunks = [assistant_reply[i:i + 2000] for i in range(0, len(assistant_reply), 2000)]

                        # Append the bot's message to the conversation history
                        self.conversations[channel_id].append({'role': 'assistant', 'content': assistant_reply})

                        # Send each chunk as a separate message
                        for chunk in reply_chunks:
                            await message.channel.send(chunk)
                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

#def setup(bot):
    #bot.add_cog(SimpleChatBot(bot))
