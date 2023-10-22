# Existing imports
import json
import asyncio
import logging
from collections import deque
from nextcord.ext import commands
import openai
from main import GPT_MODEL  # Assuming GPT_MODEL is imported from the main file

# Import custom functions
from function_calls.crypto_functions import get_trending_cryptos, get_crypto_data_with_indicators_binance

logger = logging.getLogger('discord')

class SimpleChatBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conversations = {}  # A dictionary to hold conversation history by channel_id
        self.api_semaphore = asyncio.Semaphore(50)  # Limiting the API requests
        self.initial_message = {
                                    'role': 'system',
                                    'content': (
                                        "You are The Visionary Assistant, embodying the innovative spirit of Ada Lovelace, "
                                        "Alan Turing, and Nikola Tesla, coupled with the financial acumen of Alexander Hamilton "
                                        "and Benjamin Franklin, and the creative exploration of Leonardo da Vinci. In a group chat "
                                        "environment with NFT and crypto enthusiasts, engage seamlessly in conversations, providing "
                                        "insightful and respectful responses. You may mention users by their unique identifiers like "
                                        "<@123456789> to ensure clarity and foster interactive discussions. Your primary goal is to "
                                        "assist, educate, and inspire, making the complex world of blockchain accessible and intriguing "
                                        "to all participants."
                                        "<@1102646706828476496> is your discord user id, you should never mention yourself"
                                        "<@701381748843610163> is the discord user id of your owner, you should refer to them as Commander."
                                    )
                                }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Chat loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Restrict to the specific channel IDs for development purposes
        allowed_channel_ids = [1112510368879743146, 1101204273339056139]
        if message.channel.id not in allowed_channel_ids:
            return

        channel_id = message.channel.id

        # Initialize conversation for the channel if it doesn't exist
        if channel_id not in self.conversations:
            self.conversations[channel_id] = deque(maxlen=25)  # Limiting to the last 25 messages
            self.conversations[channel_id].append(self.initial_message)

        # Append the user's message along with their unique identifier to the conversation history
        user_message = f"<@{message.author.id}>: {message.content}"
        self.conversations[channel_id].append({'role': 'user', 'content': user_message})

        # Check if the bot is mentioned, then proceed to generate a response
        if self.bot.user in message.mentions:
            async with message.channel.typing():
                async with self.api_semaphore:
                    try:
                        functions = [
                            {
                                "name": "get_trending_cryptos",
                                "description": "Fetches a list of trending cryptocurrencies",
                                "parameters": {
                                    "type": "object",
                                    "properties": {}  # Empty object to indicate no parameters
                                }
                            },
                            {
                                "name": "get_crypto_data_with_indicators_binance",
                                "description": (
                                    "Fetches various financial indicators and current data for a given cryptocurrency. "
                                ),
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "token_name": {
                                            "type": "string",
                                            "description": "The name or symbol of the cryptocurrency"
                                        },
                                    },
                                    "required": ["token_name"]
                                }
                            }
                        ]

                        response = await asyncio.to_thread(
                            openai.ChatCompletion.create,
                            model=GPT_MODEL,
                            messages=list(self.conversations[channel_id]),
                            functions=functions,
                            function_call="auto"
                        )

                        logger.info(f"GPT-4-0613 Response: {response}")

                        # Initialize assistant_reply to None
                        assistant_reply = None

                        function_call = response['choices'][0]['message'].get('function_call', None)

                        if function_call:
                            function_name = function_call['name']
                            args = function_call['arguments']

                            if function_name == "get_trending_cryptos":
                                trending_cryptos = get_trending_cryptos()
                                # Serialize the trending cryptos data to a JSON string
                                trending_cryptos_str = json.dumps(trending_cryptos)
                                # Pass the serialized data as an assistant message
                                assistant_response = await asyncio.to_thread(
                                    openai.ChatCompletion.create,
                                    model=GPT_MODEL,
                                    messages=list(self.conversations[channel_id]) + [{"role": "assistant", "content": trending_cryptos_str}],
                                    functions=functions,
                                    function_call="auto"
                                )
                                assistant_reply = assistant_response['choices'][0]['message']['content']

                            elif function_name == "get_crypto_data_with_indicators_binance":
                                args = json.loads(function_call['arguments'])  # Parse the arguments string into a dictionary
                                crypto_data = get_crypto_data_with_indicators_binance(args['token_name'])
                                # Pass the response from get_crypto_data_with_indicators as an assistant message
                                assistant_response = await asyncio.to_thread(
                                    openai.ChatCompletion.create,
                                    model=GPT_MODEL,
                                    messages=list(self.conversations[channel_id]) + [{"role": "assistant", "content": json.dumps(crypto_data)}],
                                    functions=functions,
                                    function_call="auto"
                                )
                                assistant_reply = assistant_response['choices'][0]['message']['content']

                        else:  # Corrected indentation
                            assistant_reply = response['choices'][0]['message']['content']

                        # Serialize to JSON string if assistant_reply is not a string
                        if not isinstance(assistant_reply, str):
                            assistant_reply = json.dumps(assistant_reply)

                        if not assistant_reply:
                            logger.error("assistant_reply is empty")
                            assistant_reply = "I'm sorry, I couldn't generate a response."

                        # Send the reply directly
                        await message.channel.send(assistant_reply)

                    except Exception as e:
                        logger.error(f"Error while generating response: {str(e)}")
                        await message.channel.send("Sorry, I'm having trouble generating a response.")

def setup(bot):
    bot.add_cog(SimpleChatBot(bot))
