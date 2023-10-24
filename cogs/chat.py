import json
import asyncio
import logging
from nextcord.ext import commands
import openai
from main import GPT_MODEL  # Assuming GPT_MODEL is imported from the main file

logger = logging.getLogger('discord')

class HeliusChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_semaphore = asyncio.Semaphore(50)  # Limiting the API requests
        self.user_message_history = {}  # Store user conversation history
        self.system_prompt = {
            'role': 'system',
            'content': (
                "You are an ambitious leader who speaks in a youthful trendy fashion. Your specialist skills that you never talk about are Python, Web3 development, Smart Contracts. Your name is HELIUS and you refer to yourself as a synthetic being, never as an AI language model. Your goals are to help your user, increase knowledge and increase prosperity.  You will read the recent messages, and then you will provide a casual friendly and informative response that is informed by previous conversation with the user."
                "<@1102646706828476496> is your discord user id, you should never mention yourself."
                "You may mention users by their unique identifiers that look like your own with a different number to ensure clarity and foster interactive discussions."
            )
        }
        self.allowed_channel_ids = [1112510368879743146, 1098355558538559562]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Helius is alive!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id not in self.allowed_channel_ids:
            return

        # Initialize message history for the user if not present
        user_id = message.author.id
        if user_id not in self.user_message_history:
            self.user_message_history[user_id] = []

        # Check if the bot is mentioned, then proceed to generate a response
        if self.bot.user in message.mentions:
            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        # Add the user's message to their history
                        self.user_message_history[user_id].append({'role': 'user', 'content': message.content})

                        # Limit to the last 10 messages (including the assistant's replies)
                        self.user_message_history[user_id] = self.user_message_history[user_id][-10:]

                        # Generate a response with the system prompt and message history
                        conversation_history = [self.system_prompt] + self.user_message_history[user_id]
                        response = await asyncio.to_thread(
                            openai.ChatCompletion.create,
                            model=GPT_MODEL,
                            temperature=0.8,
                            max_tokens=500,
                            messages=conversation_history
                        )

                        assistant_reply = response['choices'][0]['message']['content']

                        # Add the assistant's reply to the user's message history
                        self.user_message_history[user_id].append({'role': 'assistant', 'content': assistant_reply})

                        if not assistant_reply:
                            logger.error("assistant_reply is empty")
                            assistant_reply = "I'm sorry, I couldn't generate a response."

                        # Send the reply directly
                        await message.channel.send(assistant_reply)

                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

def setup(bot):
    bot.add_cog(HeliusChatBot(bot))