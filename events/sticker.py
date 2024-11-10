from typing import Iterable

from discord.guild import Guild
from discord.sticker import GuildSticker

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from events.utilities import ignore_unchanged_on_update
from updates.sticker import update_guild_stickers
from updates.utilities import send_notification


@bot.event
@ignore_unchanged_on_update
async def on_guild_stickers_update(
    guild: Guild,
    before: Iterable[GuildSticker],
    after: Iterable[GuildSticker],
) -> None:
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    file = await update_guild_stickers(guild_graph, after)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)
