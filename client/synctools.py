from enum import StrEnum
from typing import Tuple
from typing import Iterable
from logging import info
from logging import error
from logging import debug
from logging import warning

from rdflib.term import URIRef
from rdflib.term import Variable
from rdflib.graph import Graph
from rdflib.graph import Dataset
from rdflib.compare import to_isomorphic
from rdflib.compare import IsomorphicGraph
from rdflib.namespace import RDF

from discord.abc import GuildChannel
from discord.utils import utcnow
from discord.guild import Guild
from discord.message import Message
from discord.channel import TextChannel
from discord.channel import ForumChannel
from discord.errors import Forbidden

from client.storage import get_dataset
from client.storage import get_graph
from client.reporting import get_patches_for_notification
from client.utilities import latest_edited_at
from client.utilities import event_metadata

from model.helpers import type_uris
from model.helpers import xsd_datetime
from model.helpers import subjects_with_type
from model.namespace import DISCORD
from model.conversion import object_uri
from model.conversion import object_cbd


class SynchronisationResult(StrEnum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    UNMODIFIED = "unmodified"


async def synchronise_guilds(
    guilds: Iterable[Guild],
    sanitise: bool,
    reset: bool,
) -> None:
    """Synchronise all guild graphs with Discord state."""
    info("Synchronising all guilds with graph storage")
    start_time = utcnow()
    dataset = get_dataset()
    if reset:
        await reset_dataset(dataset)
    elif sanitise:
        await sanitise_dataset(dataset)
    variable_g = Variable("g")
    missing_guilds = set(
        URIRef(bindings[variable_g])
        for bindings in dataset.query(
            "SELECT DISTINCT ?g WHERE { GRAPH ?g { } }"
        ).bindings
    )
    info(f"Currently {len(missing_guilds)} guilds stored")
    for guild in guilds:
        guild_uri = await synchronise_guild(guild)
        if guild_uri in missing_guilds:
            missing_guilds.remove(guild_uri)
    info(f"Removing {len(missing_guilds)} previously stored guilds")
    for guild_uri in missing_guilds:
        dataset.update(f"DELETE WHERE {{ GRAPH <{guild_uri}> {{ }} }}")
        result = dataset.query(f"ASK WHERE {{ GRAPH {guild_uri} {{ }} }}")
        assert not result.askAnswer, f"Clearing failed, some triples were left"
    info(
        "Synchronisation of all guilds done in {:.2f} seconds".format(
            (utcnow() - start_time).total_seconds()
        )
    )


async def reset_dataset(dataset: Dataset) -> None:
    """Reset the entire database by removing all graphs."""
    warning("Erasing all graphs to reset the database")
    dataset.update("DELETE WHERE { GRAPH ?g { } }")
    dataset.commit()


async def sanitise_dataset(dataset: Dataset) -> None:
    """Perform some simple sanitisation tasks on the dataset."""
    warning("Sanitising dataset")
    variable_s = Variable("s")
    untyped_subjects = set(
        bindings[variable_s]
        for bindings in dataset.query(
            f"""
                SELECT DISTINCT ?s WHERE {{
                    GRAPH ?g {{
                        ?s ?p ?o .
                        FILTER NOT EXISTS {{ ?s <{RDF.type}> ?t }}
                    }}
                }}
            """
        ).bindings
    )
    for subject in untyped_subjects:
        info(f"Removing untyped <{subject}>")
        dataset.update(
            f"""
            DELETE WHERE {{
                GRAPH ?g {{
                    <{subject}> ?p ?o
                }}
            }}
            """
        )
    dataset.commit()
    info(f"Removed {len(untyped_subjects)} subjects without a type")


async def synchronise_guild(guild: Guild | URIRef) -> URIRef:
    """Synchronise an individual guild."""
    if isinstance(guild, URIRef):
        warning(f"Removing guild <{guild}>")
        dataset = get_dataset()
        dataset.update(f"REMOVE WHERE {{ GRAPH <{guild}> {{ ?s ?p ?o }} }}")
        return guild
    else:
        remote_graph = get_graph(object_uri(guild))
        start_time = utcnow()
        info(f"Synchronising guild <{remote_graph.identifier}>")
        # Create a local copy of the remove graph to speed up the synchronisation
        remote_graph_copy = Graph(identifier=remote_graph.identifier)
        remote_graph_copy += remote_graph
        local_graph = Graph(identifier=remote_graph_copy.identifier)
        local_graph += remote_graph_copy
        # Run in silent mode during initial synchronisation to avoid spam
        silent = not remote_graph_copy
        # Synchronise everything
        await synchronise_roles(local_graph, guild, silent)
        await synchronise_emojis(local_graph, guild, silent)
        await synchronise_stickers(local_graph, guild, silent)
        await synchronise_members(local_graph, guild, silent)
        await synchronise_channels(local_graph, guild, silent)
        # Determine the amount of added and removed triples
        triples_added = local_graph - remote_graph_copy
        triples_removed = remote_graph_copy - local_graph
        # Update the remote graph
        remote_graph -= triples_removed
        remote_graph += triples_added
        remote_graph.commit()
        info(
            "Synchronised in {:.2f} seconds <{}> (-{}, +{}, ={})".format(
                (utcnow() - start_time).total_seconds(),
                remote_graph.identifier,
                len(triples_removed),
                len(triples_added),
                len(remote_graph),
            )
        )
        remote_graph.close()
        return remote_graph.identifier


async def synchronise_members(graph: Graph, guild: Guild, silent: bool = False) -> None:
    """Synchronise the members of an individual guild."""
    missing_members = subjects_with_type(graph, DISCORD.User)
    for member in guild.members:
        member_uri = await synchronise(member, guild, graph, silent)
        if member_uri in missing_members:
            missing_members.remove(member_uri)
    info(f"Removing {len(missing_members)} previously stores members")
    for member_uri in missing_members:
        await synchronise(member_uri, guild, graph, silent)
    info("Synchronisation of members finished")


async def synchronise_emojis(graph: Graph, guild: Guild, silent: bool = False) -> None:
    """Synchronise the emojis of an individual guild."""
    info(f"Synchronising emojis in <{graph.identifier}>")
    missing_emojis = subjects_with_type(graph, DISCORD.Emoji)
    for emoji in guild.emojis:
        emoji_uri = await synchronise(emoji, guild, graph, silent)
        if emoji_uri in missing_emojis:
            missing_emojis.remove(emoji_uri)
    info(f"Removing {len(missing_emojis)} previously stored emojis")
    for emoji_uri in missing_emojis:
        await synchronise(emoji_uri, guild, graph, silent)
    info("Synchronisation of emojis finished")


async def synchronise_stickers(
    graph: Graph,
    guild: Guild,
    silent: bool = False,
) -> None:
    """Synchronise the stickets of an individual guild."""
    info(f"Synchronising stickets in <{graph.identifier}>")
    missing_stickers = subjects_with_type(graph, DISCORD.GuildSticker)
    for sticker in guild.stickers:
        sticker_uri = await synchronise(sticker, guild, graph, silent)
        if sticker_uri in missing_stickers:
            missing_stickers.remove(sticker_uri)
    info(f"Removing {len(missing_stickers)} previously stored stickers")
    for sticker_uri in missing_stickers:
        await synchronise(sticker_uri, guild, graph, silent)
    info("Synchronisation of stickers finished")


async def synchronise_roles(graph: Graph, guild: Guild, silent: bool = False) -> None:
    """Synchronise the roles of an individual guild."""
    info(f"Synchronising roles in <{graph.identifier}>")
    missing_roles = subjects_with_type(graph, DISCORD.Role)
    for role in guild.roles:
        role_uri = await synchronise(role, guild, graph, silent)
        if role_uri in missing_roles:
            missing_roles.remove(role_uri)
    info(f"Removing {len(missing_roles)} previously stored roles")
    for role_uri in missing_roles:
        await synchronise(role_uri, guild, graph, silent)
    info("Synchronisation of roles finished")


async def synchronise_channels(
    graph: Graph,
    guild: Guild,
    silent: bool = False,
) -> None:
    """Synchronise the channels of an individual guild."""
    info(f"Synchronising channels in <{graph.identifier}>")
    # Mapping of channel URIs to whether they need the silent flag to remove
    remove_channels = {uri: False for uri in subjects_with_type(graph, DISCORD.Channel)}
    for channel in guild.channels:
        channel_uri = object_uri(channel)
        if channel.id == guild.public_updates_channel.id:
            info(f"Skipping update channel <{channel_uri}>")
        else:
            try:
                await synchronise_channel_content(channel, guild, graph, silent)
                await synchronise(channel, guild, graph, silent)
                if channel_uri in remove_channels:
                    del remove_channels[channel_uri]
            except Forbidden:
                warning(f"Unable to access <{object_uri(channel)}>")
                if channel_uri in remove_channels:
                    remove_channels[channel_uri] = True
    info(f"Removing {len(remove_channels)} previously stored channels")
    for uri, uri_silent in remove_channels.items():
        await synchronise_channel_content(uri, guild, graph, silent or uri_silent)
        await synchronise(uri, guild, graph, silent or uri_silent)
    info("Synchronisation of channels finished")


async def synchronise_channel_content(
    channel: GuildChannel | URIRef,
    guild: Guild,
    graph: Graph,
    silent: bool = False,
) -> URIRef:
    """
    Synchronise the contents of an individual guild channel.
    If the provided channel is a URI, then it has been removed.
    If it is an object, then it still exists and has been added or modified.
    """
    channel_uri = channel if isinstance(channel, URIRef) else object_uri(channel)
    if channel_uri.endswith(str(guild.public_updates_channel.id)):
        info(f"Skipping update channel content <{channel_uri}>")
    elif not isinstance(channel, (TextChannel, ForumChannel)):
        info(f"Channel cannot not have content <{channel_uri}>")
    elif isinstance(channel, URIRef):
        info(f"Removing all content of <{channel_uri}>")
        graph.update(
            f"""
            REMOVE {{
                ?attachment ?p ?o .
            }}
            WHERE {{
                ?message <{DISCORD.channel}> <{channel_uri}> .
                ?message <{DISCORD.attachment}> ?attachment .
            }}
        """
        )
        graph.update(
            f"""
            REMOVE {{
                ?message ?p ?o .
            }}
            WHERE {{
                ?message <{DISCORD.channel}> <{channel_uri}> .
            }}
        """
        )
    elif isinstance(channel, (TextChannel, ForumChannel)):
        info(f"Synchronising message content of <{channel_uri}>")
        async for message in channel.history(limit=None, oldest_first=True):
            await synchronise(message, guild, graph, silent)
    return channel_uri


async def synchronise_message(
    message: Message | URIRef,
    guild: Guild,
    graph: Graph,
    silent: bool = False,
) -> URIRef:
    """
    Update the given message within the given guild.
    If the provided entity is a URI, then it has been deleted.
    If it is an object, then it still exists and has been added or modified.
    """
    message_uri = message if isinstance(message, URIRef) else object_uri(message)
    variable_a = Variable("a")
    missing_attachments = set(
        URIRef(bindings[variable_a])
        for bindings in graph.query(
            f"""
                SELECT DISTINCT ?a WHERE {{
                    <{message_uri}> <{DISCORD.attachment}> ?a .
                }}
            """
        ).bindings
    )
    await synchronise(message, guild, graph, silent)
    if isinstance(message, Message):
        for attachment in message.attachments:
            attachment_uri = await synchronise(attachment, guild, graph, silent)
            if attachment_uri in missing_attachments:
                missing_attachments.remove(attachment_uri)
    if missing_attachments:
        info(f"Removing {len(missing_attachments)} previously stored attachments")
        for attachment_uri in missing_attachments:
            await synchronise(attachment_uri, guild, graph, silent)
    return message_uri


async def synchronise(
    entity: object | URIRef,
    guild: Guild,
    graph: Graph,
    silent: bool = False,
) -> URIRef:
    """
    Update the given entity within the given guild, and unless the silent flag is set,
    also send an update notification to the server updates channel, containing details
    of the entity modification event.

    If the provided entity is a URI, then it has been removed.
    If it is an object, then it still exists and has been added or modified.

    The function will return the URI of the synchronised entity.
    """
    cbd = (
        IsomorphicGraph(identifier=entity)
        if isinstance(entity, URIRef)
        else object_cbd(value=entity)
    )
    assert cbd.identifier, "Synchronisation requires an entity with URI"
    result, old_cbd, new_cbd = await synchronise_cbd(cbd, graph)
    if result == SynchronisationResult.UNMODIFIED:
        debug(f"Skip notification for unmodified <{graph.identifier}>")
    else:
        types = type_uris(old_cbd, new_cbd)
        if not guild.public_updates_channel:
            error(f"Missing update channel in guild <{graph.identifier}>")
        elif silent:
            debug(f"Skip notification due to silent flag for <{cbd.identifier}>")
        elif result == SynchronisationResult.ADDED and (
            DISCORD.Message in types or DISCORD.Attachment in types
        ):
            debug(f"Skip notification for added <{cbd.identifier}>")
        else:
            info(f"Send {result.value} notification for <{cbd.identifier}>")
            try:
                await guild.public_updates_channel.send(
                    content=event_metadata(
                        event=result.value,
                        target_type=", ".join(
                            sorted(t.removeprefix(DISCORD._NS).lower() for t in types)
                        ),
                    ),
                    files=get_patches_for_notification(old_cbd, new_cbd),
                )
            except Forbidden:
                warning(f"Unable to send update notification")
    return cbd.identifier


async def synchronise_cbd(
    cbd: Graph,
    graph: Graph,
) -> Tuple[SynchronisationResult, Graph, Graph]:
    """
    Update the CBD contained within a graph to be identical with the provided one.
    This will update the graph, but also return the synchronisation result,
    alongside the old and new CBD for later use.
    """
    assert cbd.identifier, "Synchronisation of CBD requires URI identifier"
    old_cbd = to_isomorphic(graph.cbd(cbd.identifier))
    if old_cbd == cbd:
        debug(f"Unmodified <{cbd.identifier}>")
        return SynchronisationResult.UNMODIFIED, old_cbd, cbd
    else:
        # The data acquired from Discord API will not have the edit dates for most
        # objects, so the edit date needs to be acquired from the stored data.
        # The edited at date should only be added if the entire CBD is not removed.
        if cbd:
            edited_at = latest_edited_at(cbd, old_cbd)
            assert edited_at, "Update requires at least one edit date"
            cbd.set((cbd.identifier, DISCORD.editedAt, xsd_datetime(edited_at)))
        # Check which triples have been added or removed
        triples_removed = old_cbd - cbd
        triples_added = cbd - old_cbd
        # Update the graph
        graph -= triples_removed
        graph += triples_added
        # Log the update, with size information
        info(
            "Synced <{}> (-{}, +{}, ={})".format(
                cbd.identifier,
                len(triples_removed),
                len(triples_added),
                len(cbd),
            )
        )
        return (
            (
                SynchronisationResult.ADDED
                if not old_cbd
                else (
                    SynchronisationResult.REMOVED
                    if not cbd
                    else SynchronisationResult.MODIFIED
                )
            ),
            old_cbd,
            cbd,
        )
