from discord.scheduled_events import ScheduledEvent

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from events.utilities import ignore_unchanged_on_update
from updates.shared import update_entity
from updates.shared import delete_entity
from updates.utilities import send_notification


@bot.event
async def on_scheduled_event_create(event: ScheduledEvent) -> None:
    guild_uri = uri(event.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, event)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(event.guild, file)


@bot.event
@ignore_unchanged_on_update
async def on_scheduled_event_update(
    before: ScheduledEvent,
    after: ScheduledEvent,
) -> None:
    guild_uri = uri(after.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, after)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(after.guild, file)


@bot.event
async def on_scheduled_event_delete(event: ScheduledEvent) -> None:
    guild_uri = uri(event.guild)
    event_uri = uri(event)
    guild_graph = await graph(guild_uri)
    file = await delete_entity(guild_graph, event_uri)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(event.guild, file)
