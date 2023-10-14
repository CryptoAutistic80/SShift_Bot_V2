import nextcord
from nextcord.ext import commands
from langdetect import detect, LangDetectException

CHANNEL = 1112510368879743146

class Translator(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Translator ready")

    @commands.Cog.listener()
    async def on_message(self, message):
      if message.channel.id == CHANNEL and not message.author.bot:
          try:
              lang = detect(message.content)
              if lang != 'en':
                  await message.add_reaction('🌎')
          except LangDetectException:
              print("Could not determine the language.")

def setup(client):
    client.add_cog(Translator(client))