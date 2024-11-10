from typing import Set
from typing import Optional
from typing import Iterable
from logging import info
from logging import debug
from logging import warning

from rdflib.term import URIRef
from rdflib.term import Variable
from rdflib.graph import Graph
from rdflib.namespace import RDF

from discord.file import File
from discord.guild import Guild
from discord.utils import utcnow

from graph.patch import patch
from graph.convert import uri
from graph.convert import cbd
from graph.storage import graph
from graph.storage import dataset
from graph.utilities import copy
from graph.vocabulary import DISCORD
from updates.channel import collect_channel
from updates.channel import collect_channel_graph
from updates.utilities import send_notification


async def update_guild(guild: Guild, validate_content: bool = False) -> Optional[File]:
    """Updates the stored guild."""

    after = cbd(guild)
    guild_graph = await graph(after.identifier)

    if validate_content:
        info(f"Updating content for guild <{after.identifier}>")

        before = await copy(guild_graph)

        for role in guild.roles:
            after += cbd(role)

        for member in guild.members:
            after += cbd(member)

        for emoji in guild.emojis:
            after += cbd(emoji)

        for sticker in guild.stickers:
            after += cbd(sticker)

        for event in guild.scheduled_events:
            after += cbd(event)

        for channel in guild.channels:
            if channel.id != guild.public_updates_channel.id:
                after += await collect_channel(channel)

    else:
        before = guild_graph.cbd(after.identifier)

    file = await patch(guild_graph, before, after)

    guild_graph.commit()
    guild_graph.close()

    after.close()
    before.close()

    return file


async def delete_guild(guild_uri: URIRef) -> None:
    """Deletes the stored guild."""

    warning(f"Removing guild graph <{guild_uri}>")

    default_dataset = await dataset()

    default_dataset.update(
        f"""
            DELETE WHERE {{
                GRAPH <{guild_uri}> {{
                    ?s ?p ?o
                }}
            }}
        """
    )

    result = default_dataset.query(
        f"""
            ASK WHERE {{
                GRAPH <{guild_uri}> {{
                    ?s ?p ?o
                }}
            }}
        """
    )

    assert not result.askAnswer, "Removal of guild graph failed"

    default_dataset.commit()


async def synchronise_guilds(guilds: Iterable[Guild]) -> None:
    """Synchronises the set of stored guilds to the provided one."""

    start_time = utcnow()

    info("Synchronising all guilds with Discord state")

    guild_uris = await stored_guild_uris()

    for guild in guilds:
        file = await update_guild(guild, validate_content=True)
        await send_notification(guild, file)
        guild_uri = uri(guild)
        if guild_uri in guild_uris:
            guild_uris.remove(guild_uri)

    for guild_uri in guild_uris:
        await delete_guild(guild_uri)

    info(
        "Synchronised all guilds in {:.2f} seconds".format(
            (utcnow() - start_time).total_seconds(),
        )
    )


async def refresh_channels(guild: Guild) -> Optional[File]:
    """Refresh channel after permission update, if deemed relevant."""

    guild_uri = uri(guild)

    info(f"Refreshing channels in <{guild_uri}>")

    guild_graph = await graph(guild_uri)
    guild_graph_copy = await copy(guild_graph)

    channel_uris = set(
        guild_graph_copy.subjects(
            predicate=RDF.type,
            object=DISCORD.Channel,
            unique=True,
        )
    )

    graph_before = Graph()
    graph_after = Graph()

    for channel in guild.channels:
        channel_uri = uri(channel)
        if (
            guild.public_updates_channel
            and channel.id == guild.public_updates_channel.id
        ):
            debug(f"Skip updates channel <{channel_uri}>")
        else:
            if channel_uri in channel_uris:
                channel_uris.remove(channel_uri)
                debug(f"Update existing <{channel_uri}>")
                graph_before += await collect_channel_graph(
                    guild_graph_copy,
                    channel_uri,
                )
            else:
                debug(f"Found new <{channel_uri}>")
            graph_after += await collect_channel(channel)

    for channel_uri in channel_uris:
        debug(f"Remove previously seen <{channel_uri}>")
        graph_before += await collect_channel_graph(guild_graph_copy, channel_uri)

    file = await patch(guild_graph, graph_before, graph_after)

    guild_graph.commit()
    guild_graph.close()

    graph_before.close()
    graph_after.close()

    return file


async def stored_guild_uris() -> Set[URIRef]:
    """Collect the URIs of all guilds currently stored."""

    default_dataset = await dataset()

    variable_g = Variable("g")

    result = default_dataset.query("SELECT DISTINCT ?g WHERE { GRAPH ?g { } }")

    guild_uris = set(bindings[variable_g] for bindings in result.bindings)

    return guild_uris
