from typing import Optional
from typing import Coroutine
from logging import debug
from functools import wraps

from rdflib.compare import IsomorphicGraph
from rdflib.compare import to_isomorphic

from discord.abc import GuildChannel
from discord.guild import Guild
from discord.threads import Thread
from discord.message import Message
from discord.raw_models import RawMessageDeleteEvent
from discord.raw_models import RawMessageUpdateEvent
from discord.raw_models import RawBulkMessageDeleteEvent
from discord.raw_models import RawThreadDeleteEvent
from discord.raw_models import RawThreadUpdateEvent
from discord.raw_models import RawMemberRemoveEvent

from client.bot import bot
from graph.convert import uri
from graph.convert import cbd


def ignore_public_updates_channel(func: Coroutine) -> Coroutine:
    """Wrapper to ignore events in the public updates channel."""

    @wraps(func)
    async def ignore_public_updates_channel_wrapper(*args, **kwargs) -> None:
        channel_id: Optional[int] = None
        guild: Optional[Guild] = None

        if isinstance(args[0], Thread):
            channel_id = args[0].parent_id
            guild = args[0].guild
        elif isinstance(args[0], GuildChannel):
            channel_id = args[0].id
            guild = args[0].guild
        elif isinstance(args[0], Message):
            channel_id = args[0].channel.id
            guild = args[0].guild
        elif isinstance(args[0], RawThreadDeleteEvent):
            channel_id = args[0].parent_id
            guild = bot.get_guild(args[0].guild_id)
        elif isinstance(
            args[0],
            (
                RawMessageDeleteEvent,
                RawMessageUpdateEvent,
                RawBulkMessageDeleteEvent,
                RawThreadUpdateEvent,
            ),
        ):
            channel_id = args[0].channel_id
            guild = bot.get_guild(args[0].guild_id)

        if (
            channel_id
            and guild
            and guild.public_updates_channel
            and channel_id == guild.public_updates_channel.id
        ):
            debug(f"Ignoring {func.__name__} in updates channel of <{uri(guild)}>")
        else:
            return await func(*args, *kwargs)

    return ignore_public_updates_channel_wrapper


def ignore_unchanged_on_update(func: Coroutine) -> Coroutine:
    """Wrapper to ignore update events that do not modify the graph."""

    @wraps(func)
    async def ignore_unchanged_on_update_wrapper(*args, **kwargs) -> None:
        cbd_first = None
        cbd_second = None
        if len(args) > 1 and type(args[0]) == type(args[1]):
            cbd_first = to_isomorphic(cbd(args[0]))
            cbd_second = to_isomorphic(cbd(args[1]))
        elif len(args) > 2 and type(args[1]) == type(args[2]):
            cbd_first = IsomorphicGraph()
            cbd_second = IsomorphicGraph()
            for value in args[1]:
                cbd_first += cbd(value)
            for value in args[2]:
                cbd_second += cbd(value)
        unchanged = cbd_first == cbd_second if cbd_first is not None else False
        if unchanged:
            debug(f"Ignoring {func.__name__} for unchanged <{cbd_first.identifier}>")
        else:
            return await func(*args, **kwargs)

    return ignore_unchanged_on_update_wrapper


def find_guild(
    payload: (
        RawMessageDeleteEvent
        | RawMessageUpdateEvent
        | RawBulkMessageDeleteEvent
        | RawThreadDeleteEvent
        | RawThreadUpdateEvent
        | RawMemberRemoveEvent
    ),
) -> Guild:
    """Finds the guild from a raw Discord event, based on the event guild_id."""
    assert payload.guild_id, "Missing guild_id in raw event payload"
    payload_guild = bot.get_guild(payload.guild_id)
    assert payload_guild, f"Unable to find guild with id {payload.guild_id}"
    return payload_guild
