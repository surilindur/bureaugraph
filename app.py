from discord import Intents

from client.config import get_discord_token
from client.config import get_log_level
from client.client import CustomClient

intents = Intents.none()
intents.guild_messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

client = CustomClient(intents=intents)

if __name__ == "__main__":
    client.run(
        reconnect=True,
        token=get_discord_token(),
        log_level=get_log_level(),
        root_logger=True,
    )
