from discord.threads import Thread
from discord.raw_models import RawThreadDeleteEvent
from discord.raw_models import RawThreadUpdateEvent

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from graph.utilities import create_thread_uri
from events.utilities import find_guild
from events.utilities import ignore_public_updates_channel
from updates.channel import update_channel
from updates.channel import delete_channel
from updates.utilities import send_notification


@bot.event
@ignore_public_updates_channel
async def on_thread_create(thread: Thread) -> None:
    guild_uri = uri(thread.guild)
    guild_graph = await graph(guild_uri)
    file = await update_channel(guild_graph, thread)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(thread.guild, file)


@bot.event
@ignore_public_updates_channel
async def on_raw_thread_update(payload: RawThreadUpdateEvent) -> None:
    guild = find_guild(payload)
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    thread = bot.get_channel(payload.thread_id)
    file = await update_channel(guild_graph, thread)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)


@bot.event
@ignore_public_updates_channel
async def on_raw_thread_delete(payload: RawThreadDeleteEvent) -> None:
    guild = find_guild(payload)
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    thread_uri = await create_thread_uri(payload.guild_id, payload.thread_id)
    file = await delete_channel(guild_graph, thread_uri)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)
