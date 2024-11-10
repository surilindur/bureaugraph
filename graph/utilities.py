from enum import StrEnum
from logging import warning
from datetime import datetime
from urllib.parse import urlparse
from urllib.error import HTTPError

from rdflib.term import URIRef
from rdflib.graph import Graph

from graph.convert import python_datetime
from graph.vocabulary import DISCORD
from graph.vocabulary import DISCORD_URI


class SerializationFormat(StrEnum):
    HEXT = "hext"
    JSONLD = "json-ld"
    N3 = "n3"
    NQUADS = "nquads"
    NT = "nt"
    PRETTYXML = "pretty-xml"
    TRIG = "trig"
    TRIX = "trix"
    TURTLE = "turtle"
    XML = "xml"


async def copy(graph: Graph) -> Graph:
    """Creates a local copy of a graph, mostly for performance reasons."""

    assert graph.identifier, "Attempting to copy a graph without identifier"

    local_graph = Graph(identifier=graph.identifier)

    try:
        local_graph += graph
    except HTTPError:
        # When requesting a non-existing graph, the server seems to send status 400
        warning(f"Creating a local copy of empty gaph <{graph.identifier}>")

    return local_graph


async def edited(*graphs: Graph) -> datetime | None:
    """Finds the latest edited_at date from graphs."""

    latest_edit = None

    for graph in graphs:
        for object in graph.objects(predicate=DISCORD.editedAt, unique=True):
            object_datetime = python_datetime(object)
            if not latest_edit or object_datetime > latest_edit:
                latest_edit = object_datetime

    return latest_edit


async def serialize(
    graph: Graph,
    format: SerializationFormat = SerializationFormat.TURTLE,
) -> str:
    """Serializes the graph, with the proper prefix bindings."""

    graph.bind("discord", DISCORD)

    return graph.serialize(format=format.value)


async def create_message_uri(guild_id: int, channel_id: int, message_id: int) -> URIRef:
    """Constructs a message URI from numeric identifiers."""
    return URIRef(f"{DISCORD_URI}/channels/{guild_id}/{channel_id}/{message_id}")


async def create_thread_uri(guild_id: int, thread_id: int) -> URIRef:
    """Constructs a thread URI from numeric identifiers."""
    return URIRef(f"{DISCORD_URI}/channels/{guild_id}/{thread_id}")


async def parse_discord_uri(uri: str) -> URIRef:
    """Parses and validates a Discord URI."""

    parsed = urlparse(uri.strip())

    assert parsed.scheme == "https", f"Invalid URI scheme: {parsed.scheme}"
    assert parsed.hostname == "discord.com", f"Invalid URI host: {parsed.hostname}"
    assert not parsed.query, f"Unnecessaru query string: {parsed.query}"
    assert not parsed.fragment, f"Unnecessary fragment: {parsed.fragment}"

    return URIRef(parsed.geturl())
