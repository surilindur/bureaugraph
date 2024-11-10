from discord.role import Role

from client.bot import bot
from graph.convert import uri
from graph.storage import graph
from events.utilities import ignore_unchanged_on_update
from updates.guild import refresh_channels
from updates.shared import update_entity
from updates.shared import delete_entity
from updates.utilities import send_notification


@bot.event
async def on_guild_role_create(role: Role) -> None:
    guild_uri = uri(role.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, role)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(role.guild, file)


@bot.event
async def on_guild_role_delete(role: Role) -> None:
    guild_uri = uri(role.guild)
    guild_graph = await graph(guild_uri)
    file = await delete_entity(guild_graph, role)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(role.guild, file)


@bot.event
@ignore_unchanged_on_update
async def on_guild_role_update(before: Role, after: Role) -> None:
    guild_uri = uri(after.guild)
    guild_graph = await graph(guild_uri)
    file = await update_entity(guild_graph, after)
    guild_graph.commit()
    guild_graph.close()
    await send_notification(after.guild, file)
    bot_member = after.guild.get_member(bot.user.id)
    if bot_member and after in bot_member.roles:
        file = await refresh_channels(after.guild)
        await send_notification(after.guild, file)
