# ________  ________      ___    ___ ________  _________  ________          ________  ___  ___  _________  ___  ________  _________  ___  ________         
#|\   ____\|\   __  \    |\  \  /  /|\   __  \|\___   ___\\   __  \        |\   __  \|\  \|\  \|\___   ___\\  \|\   ____\|\___   ___\\  \|\   ____\        
#\ \  \___|\ \  \|\  \   \ \  \/  / | \  \|\  \|___ \  \_\ \  \|\  \       \ \  \|\  \ \  \\\  \|___ \  \_\ \  \ \  \___|\|___ \  \_\ \  \ \  \___|        
# \ \  \    \ \   _  _\   \ \    / / \ \   ____\   \ \  \ \ \  \\\  \       \ \   __  \ \  \\\  \   \ \  \ \ \  \ \_____  \   \ \  \ \ \  \ \  \           
#  \ \  \____\ \  \\  \|   \/  /  /   \ \  \___|    \ \  \ \ \  \\\  \       \ \  \ \  \ \  \\\  \   \ \  \ \ \  \|____|\  \   \ \  \ \ \  \ \  \____      
#   \ \_______\ \__\\ _\ __/  / /      \ \__\        \ \__\ \ \_______\       \ \__\ \__\ \_______\   \ \__\ \ \__\____\_\  \   \ \__\ \ \__\ \_______\    
#    \|_______|\|__|\|__|\___/ /        \|__|         \|__|  \|_______|        \|__|\|__|\|_______|    \|__|  \|__|\_________\   \|__|  \|__|\|_______|    
#                      \|___|/                                                                                   \|_________|                             


#          ___  _____ ______   ________  ________  ___  ________   _______   _______   ________                                                           
#         |\  \|\   _ \  _   \|\   __  \|\   ____\|\  \|\   ___  \|\  ___ \ |\  ___ \ |\   __  \                                                          
#         \ \  \ \  \\\__\ \  \ \  \|\  \ \  \___|\ \  \ \  \\ \  \ \   __/|\ \   __/|\ \  \|\  \                                                         
#          \ \  \ \  \\|__| \  \ \   __  \ \  \  __\ \  \ \  \\ \  \ \  \_|/_\ \  \_|/_\ \   _  _\                                                        
#           \ \  \ \  \    \ \  \ \  \ \  \ \  \|\  \ \  \ \  \\ \  \ \  \_|\ \ \  \_|\ \ \  \\  \|                                                       
#            \ \__\ \__\    \ \__\ \__\ \__\ \_______\ \__\ \__\\ \__\ \_______\ \_______\ \__\\ _\                                                       
#             \|__|\|__|     \|__|\|__|\|__|\|_______|\|__|\|__| \|__|\|_______|\|_______|\|__|\|__|    
#
# SShift DAO - 2023 
# http://www.sshift.xyz
# Bot server: https://sshift-bot-v2.cryptoautistic8.repl.co
#
import logging
import logging.handlers
import os

import nextcord
from nextcord.ext import commands, application_checks
import openai

from database.database_manager import initialize_db, add_guild, remove_guild
from server import start_server

# Initialize the OpenAI API
openai.api_key = os.environ['OPENAI_KEY']

# Set Constants
GPT_MODEL = "gpt-4-0613"
TRAN_GPT_MODEL = "gpt-3.5-turbo"

def setup_logging():
    """Configure logging for the bot."""
    logger = logging.getLogger('discord')
    logger.setLevel(logging.DEBUG)
    
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

@bot.event
async def on_application_command_error(interaction, error):
    if isinstance(error, application_checks.ApplicationMissingPermissions):
        await interaction.response.send_message(
            "Whoooa let’s set some boundaries, you don't have permission to touch me there sorry",
            ephemeral=True
        )

# Load cogs
load_cogs(bot, logger)

# Start the FastAPI server to keep the Replit project awake
start_server()

# Start the bot
bot.run(os.getenv('DISCORD_TOKEN'))