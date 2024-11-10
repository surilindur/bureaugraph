from typing import Iterable

from discord.guild import Guild
from discord.emoji import Emoji

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from events.utilities import ignore_unchanged_on_update
from updates.emoji import update_emojis
from updates.utilities import send_notification


@bot.event
@ignore_unchanged_on_update
async def on_guild_emojis_update(
    guild: Guild,
    before: Iterable[Emoji],
    after: Iterable[Emoji],
) -> None:
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    file = await update_emojis(guild_graph, after)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)
