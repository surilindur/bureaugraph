from logging import debug

from discord.abc import GuildChannel

from client.bot import bot
from graph.convert import uri
from graph.convert import cbd
from graph.storage import graph
from events.utilities import ignore_public_updates_channel
from updates.channel import update_channel
from updates.channel import delete_channel
from updates.utilities import send_notification


@bot.event
@ignore_public_updates_channel
async def on_guild_channel_create(channel: GuildChannel) -> None:
    guild_uri = uri(channel.guild)
    guild_graph = await graph(guild_uri)
    file = await update_channel(guild_graph, channel)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(channel.guild, file)


@bot.event
@ignore_public_updates_channel
async def on_guild_channel_delete(channel: GuildChannel) -> None:
    guild_uri = uri(channel.guild)
    guild_graph = await graph(guild_uri)
    channel_uri = uri(channel)
    file = await delete_channel(guild_graph, channel_uri)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(channel.guild, file)


@bot.event
@ignore_public_updates_channel
async def on_guild_channel_update(before: GuildChannel, after: GuildChannel) -> None:
    should_consider_event = cbd(before) != cbd(after)
    if not should_consider_event:
        bot_member = after.guild.get_member(bot.user.id)
        before_permissions = before.permissions_for(bot_member)
        after_permissions = after.permissions_for(bot_member)
        should_consider_event = before_permissions != after_permissions
        debug(f"Refresh channel due to bot permission update")
    if should_consider_event:
        debug(f"Updated <{uri(after)}>")
        guild_uri = uri(after.guild)
        guild_graph = await graph(guild_uri)
        file = await update_channel(guild_graph, after)
        guild_graph.commit()
        guild_graph.close()
        await send_notification(after.guild, file)
    else:
        debug(f"Skip unmodified <{uri(after)}>")
