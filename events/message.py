from discord.message import Message
from discord.raw_models import RawMessageDeleteEvent
from discord.raw_models import RawMessageUpdateEvent
from discord.raw_models import RawBulkMessageDeleteEvent

from client.bot import bot
from events.utilities import find_guild
from events.utilities import ignore_public_updates_channel
from graph.convert import uri
from graph.storage import graph
from graph.utilities import create_message_uri
from updates.message import update_message
from updates.message import delete_message
from updates.message import bulk_delete_messages
from updates.utilities import send_notification


@bot.event
@ignore_public_updates_channel
async def on_message(message: Message) -> None:
    guild_uri = uri(message.guild)
    guild_graph = await graph(guild_uri)
    file = await update_message(guild_graph, message)
    guild_graph.commit()
    guild_graph.close()
    # Logging every new message would get really spammy really fast
    # await send_notification(message.guild, file)


@bot.event
@ignore_public_updates_channel
async def on_raw_message_edit(payload: RawMessageUpdateEvent) -> None:
    guild = find_guild(payload)
    channel = bot.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    file = await update_message(guild_graph, message)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)


@bot.event
@ignore_public_updates_channel
async def on_raw_message_delete(payload: RawMessageDeleteEvent) -> None:
    guild = find_guild(payload)
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    message_uri = await create_message_uri(
        payload.guild_id,
        payload.channel_id,
        payload.message_id,
    )
    file = await delete_message(guild_graph, message_uri)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)


@bot.event
@ignore_public_updates_channel
async def on_raw_bulk_message_delete(payload: RawBulkMessageDeleteEvent) -> None:
    guild = find_guild(payload)
    guild_uri = uri(guild)
    guild_graph = await graph(guild_uri)
    message_uris = set(
        await create_message_uri(payload.guild_id, payload.channel_id, msg_id)
        for msg_id in payload.message_ids
    )
    file = await bulk_delete_messages(guild_graph, message_uris)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(guild, file)
