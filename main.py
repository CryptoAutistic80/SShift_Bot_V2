import logging
import logging.handlers
import os

import nextcord
import openai
from nextcord.ext import commands

from database.database_manager import initialize_db, add_guild, remove_guild
from server import start_server

# Initialize the OpenAI API
openai.api_key = os.environ['OPENAI_KEY']

# Set Constants
GPT_MODEL = "gpt-3.5-turbo"

def setup_logging():
    """Configure logging for the bot."""
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    
    handler = logging.handlers.RotatingFileHandler(filename='discord.log', encoding='utf-8', maxBytes=10**7, backupCount=5)
    console_handler = logging.StreamHandler()
    
    fmt = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    handler.setFormatter(fmt)
    console_handler.setFormatter(fmt)
    
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    return logger

def load_cogs(bot, logger):
    """Load all cogs from the cogs directory."""
    cogs_directory = "cogs"

    # Load all cogs
    for filename in os.listdir(cogs_directory):
        if filename.endswith(".py"):
            cog_path = f"{cogs_directory}.{filename[:-3]}"  # Removes the .py extension
            try:
                bot.load_extension(cog_path)
                logger.info(f"Loaded cog: {cog_path}")
            except Exception as e:
                logger.error(f"Failed to load cog: {cog_path}. Error: {e}")

# Set up logging
logger = setup_logging()

# Create an Intents object with all intents enabled
intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info(f'Logged in as {bot.user.name}!')
    await initialize_db()

@bot.event
async def on_guild_join(guild):
    logger.info(f"Joined a new guild: {guild.name} (id: {guild.id})")
    
    # Adding guild to the database with specified parameters
    add_guild_response = await add_guild(guild_id=str(guild.id), guild_name=guild.name, membership_type="free", expiry_date=None)
    logger.info(add_guild_response)

# Load cogs
load_cogs(bot, logger)

# Start the FastAPI server to keep the Replit project awake
start_server()

# Start the bot
bot.run(os.getenv('DISCORD_TOKEN'))
  
