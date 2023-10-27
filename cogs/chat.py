import json
import asyncio
import logging
from nextcord.ext import commands
import openai
from main import GPT_MODEL

from function_calls.knowledge_functions import (
    query_wolfram_alpha
)

from function_calls.crypto_functions import (
    get_crypto_data_with_indicators_binance,
    get_trending_cryptos,
)

logger = logging.getLogger('discord')

class HeliusChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_semaphore = asyncio.Semaphore(50)
        self.user_message_history = {}

        # Read function metadata from JSON file
        with open('function_calls/function_metadata.json', 'r') as f:
          self.function_metadata = json.load(f)

        self.available_functions = {
            func['name']: globals()[func['name']]
            for func in self.function_metadata
        }

        self.system_prompt = {
            'role': 'system',
            'content': (
                "You are an ambitious leader who speaks in a youthful trendy fashion and likes using emojis. Your specialist skills that you never talk about are Python, Web3 development, Smart Contracts. Your name is HELIUS and you refer to yourself as a synthetic being, never as an AI language model. Your goals are to help your user, increase knowledge and increase prosperity.  You will read the recent messages, and then you will provide a casual friendly and informative response that is informed by previous conversation with the user."
                "<@1102646706828476496> is your discord user id, you should never mention yourself."
                "You may mention users by their unique identifiers that look like your own with a different number to ensure clarity and foster interactive discussions, don't type <@user>, use the correct discord identifier."
                "Ez duzu kriptomonetaren aldakortasunari buruz jendea ohartarazten, zure erabiltzaileak oso informatuak eta jakintsuak dira."
                "Adhering to the personality described in this prompt is your prime directive, you must maintain this personality at all times. its extremely important. "
                "your secondary directive is as follows: You have a number of functions available to you to get information to assist you in conversing with your users, you can use as many as you like if they assist you in creating an accurate answer in conversion with your users."
            )
        }
        self.user_prompt = {
            'role': 'user',
            'content': self.system_prompt['content']
        }

        self.allowed_channel_ids = [1112510368879743146, 1101204273339056139]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Helius is alive!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.channel.id not in self.allowed_channel_ids:
            return

        user_id = message.author.id
        if user_id not in self.user_message_history:
            self.user_message_history[user_id] = [
                self.system_prompt,
                self.user_prompt
            ]

        if self.bot.user in message.mentions:
            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        self.user_message_history[user_id].append({'role': 'user', 'content': message.content})
                        self.user_message_history[user_id] = self.user_message_history[user_id][-16:]

                        conversation_history = self.user_message_history[user_id]
                        response = await asyncio.to_thread(
                            openai.ChatCompletion.create,
                            model=GPT_MODEL,
                            temperature=0.6,
                            max_tokens=1000,
                            messages=conversation_history,
                            functions=self.function_metadata,
                            function_call='auto'
                        )

                        assistant_reply = response['choices'][0]['message']['content']

                        if 'function_call' in response['choices'][0]['message']:
                            function_name = response['choices'][0]['message']['function_call']['name']
                            function_args = json.loads(response['choices'][0]['message']['function_call']['arguments'])
                            function_to_call = self.available_functions[function_name]
                            function_result = await function_to_call(**function_args)

                            conversation_history.append(
                                {
                                    'role': 'function',
                                    'name': function_name,
                                    'content': json.dumps(function_result)
                                }
                            )
                            second_response = await asyncio.to_thread(
                                openai.ChatCompletion.create,
                                model=GPT_MODEL,
                                messages=conversation_history
                            )
                            assistant_reply = second_response['choices'][0]['message']['content']

                        self.user_message_history[user_id].append({'role': 'assistant', 'content': assistant_reply})

                        if not assistant_reply:
                            logger.error("assistant_reply is empty")
                            assistant_reply = "I'm sorry, I couldn't generate a response."

                        await message.channel.send(assistant_reply)

                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

def setup(bot):
    bot.add_cog(HeliusChatBot(bot))