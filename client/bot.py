from discord import Intents
from discord.bot import Bot
from discord.enums import Status
from discord.activity import CustomActivity

# Define the gateway intents
intents = Intents.none()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.members = True
intents.emojis_and_stickers = True
intents.scheduled_events = True

# Create the bot
bot = Bot(
    intents=intents,
    max_messages=None,  # Disable the internal message cache entirely
    activity=CustomActivity(
        name="Synchronising",
        extra="Retroactively registering modifications",
    ),
    status=Status.dnd,
)
