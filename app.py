from discord import Intents

from src.config import DISCORD_TOKEN, HISTORY_MINIMUM
from src.client import App

if __name__ == "__main__":
    intents = Intents.default()
    intents.message_content = True
    client = App(intents=intents, max_messages=HISTORY_MINIMUM)
    client.run(token=DISCORD_TOKEN)
