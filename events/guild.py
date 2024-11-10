from logging import warning

from discord.guild import Guild

from client.bot import bot
from graph.convert import uri
from events.utilities import ignore_unchanged_on_update
from updates.guild import update_guild
from updates.guild import delete_guild
from updates.utilities import send_notification


@bot.event
async def on_guild_join(guild: Guild) -> None:
    guild_uri = uri(guild)
    warning(f"Joined guild <{guild_uri}>")
    file = await update_guild(guild, validate_content=True)
    await send_notification(guild, file)


@bot.event
@ignore_unchanged_on_update
async def on_guild_update(before: Guild, after: Guild) -> None:
    file = await update_guild(after, validate_content=False)
    await send_notification(after, file)


@bot.event
async def on_guild_remove(guild: Guild) -> None:
    guild_uri = uri(guild)
    warning(f"Left guild <{guild_uri}>")
    await delete_guild(guild_uri)
