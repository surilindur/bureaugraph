from typing import Optional
from logging import warning

from rdflib.term import URIRef
from rdflib.graph import Graph

from discord.abc import GuildChannel
from discord.file import File
from discord.errors import Forbidden
from discord.threads import Thread
from discord.channel import TextChannel
from discord.channel import ForumChannel

from graph.patch import patch
from graph.convert import uri
from graph.convert import cbd
from graph.utilities import copy
from graph.vocabulary import DISCORD


async def update_channel(
    graph: Graph,
    channel: GuildChannel | Thread,
) -> Optional[File]:
    """Updates the stored channel or thread."""

    channel_uri = uri(channel)

    before = await collect_channel_graph(graph, channel_uri)
    after = await collect_channel(channel)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file


async def delete_channel(graph: Graph, channel_uri: URIRef) -> Optional[File]:
    """Deletes the stored channel."""

    after = Graph()
    before = await collect_channel_graph(graph, channel_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file


async def collect_channel(channel: GuildChannel | Thread) -> Graph:
    """
    Collects the full channel description from the Discord API,
    including messages, attachments and threads for the relevant channel types.
    """

    content = cbd(channel)

    try:
        if isinstance(channel, (TextChannel, Thread)):
            async for message in channel.history(limit=None, oldest_first=True):
                content += cbd(message)
                for attachment in message.attachments:
                    content += cbd(attachment)
                if message.thread:
                    content += await collect_channel(message.thread)

        elif isinstance(channel, ForumChannel):
            for thread in channel.threads:
                content += await collect_channel(thread)

    except Forbidden:
        warning(f"Missing permissions for content in <{uri(channel)}>")

    return content


async def collect_channel_graph(graph: Graph, channel_uri: URIRef) -> Graph:
    """
    Collects the full stored channel graph from the database,
    including messages, attachments and threads for the channels that can have them.
    """

    # Local copy is needed for performance reasons
    local_graph = await copy(graph)

    content = Graph()

    stored_channel_uris = set(
        (
            channel_uri,
            *local_graph.subjects(
                predicate=DISCORD.parent,
                object=channel_uri,
                unique=True,
            ),
        )
    )

    for stored_channel_uri in stored_channel_uris:
        content += local_graph.cbd(stored_channel_uri)
        for message_uri in local_graph.subjects(
            predicate=DISCORD.channel,
            object=stored_channel_uri,
            unique=True,
        ):
            content += local_graph.cbd(message_uri)
            for attachment_uri in local_graph.objects(
                subject=message_uri,
                predicate=DISCORD.attachment,
                unique=True,
            ):
                content += local_graph.cbd(attachment_uri)

    local_graph.close()

    return content
