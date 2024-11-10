from logging import warning

from discord.member import Member
from discord.raw_models import RawMemberRemoveEvent

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from events.utilities import ignore_unchanged_on_update
from events.utilities import find_guild
from updates.guild import refresh_channels
from updates.shared import update_entity
from updates.shared import delete_entity
from updates.utilities import send_notification


@bot.event
async def on_member_join(member: Member) -> None:
    guild_uri = uri(member.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, member)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(member.guild, file)


@bot.event
async def on_raw_member_remove(payload: RawMemberRemoveEvent) -> None:
    if payload.user.id != bot.user.id:
        guild = find_guild(payload)
        guild_uri = uri(guild)
        member_uri = uri(payload.user)
        guild_graph = await graph(guild_uri)
        file = await delete_entity(guild_graph, member_uri)
        guild_graph.commit()
        guild_graph.close()
        await send_notification(guild, file)
    else:
        warning("Ignoring raw member remove event for bot user")


@bot.event
@ignore_unchanged_on_update
async def on_member_update(before: Member, after: Member) -> None:
    guild_uri = uri(after.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, after)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(after.guild, file)
    if after.id == bot.user.id:
        file = await refresh_channels(after.guild)
        await send_notification(after.guild, file)
