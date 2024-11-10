from typing import Iterable

from rdflib.term import URIRef
from rdflib.graph import Graph

from discord.file import File
from discord.message import Message

from graph.patch import patch
from graph.convert import cbd
from graph.vocabulary import DISCORD


async def update_message(graph: Graph, message: Message) -> File:
    """Updates the stored message and its attachments to the provided one."""

    after = cbd(message)
    before = graph.cbd(after.identifier)

    attachment_uris = set(before.objects(predicate=DISCORD.attachment, unique=True))

    for attachment in message.attachments:
        attachment_cbd = cbd(attachment)
        after += attachment_cbd
        before += graph.cbd(attachment_cbd.identifier)
        if attachment_cbd.identifier in attachment_uris:
            attachment_uris.remove(attachment_cbd.identifier)

    for attachment_uri in attachment_uris:
        before += graph.cbd(attachment_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file


async def delete_message(graph: Graph, message_uri: URIRef) -> File:
    """Deletes the stored message and its attachments."""

    after = Graph()
    before = graph.cbd(message_uri)

    attachment_uris = set(before.objects(predicate=DISCORD.attachment, unique=True))

    for attachment_uri in attachment_uris:
        before += graph.cbd(attachment_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file


async def bulk_delete_messages(graph: Graph, message_uris: Iterable[URIRef]) -> File:
    """Deletes all stored messages and their attachments."""

    after = Graph()
    before = Graph()

    for message_uri in message_uris:
        before += graph.cbd(message_uri)

    for attachment_uri in before.objects(predicate=DISCORD.attachment, unique=True):
        before += graph.cbd(attachment_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file
