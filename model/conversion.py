from typing import List
from typing import Tuple
from typing import Iterable
from datetime import datetime
from urllib.parse import urljoin
from urllib.parse import urlparse

from discord.abc import GuildChannel
from discord.role import Role
from discord.user import User
from discord.user import ClientUser
from discord.guild import Guild
from discord.member import Member
from discord.message import Message
from discord.message import Attachment
from discord.channel import TextChannel
from discord.channel import VoiceChannel
from discord.channel import ForumChannel

from rdflib.term import URIRef
from rdflib.term import Literal
from rdflib.graph import Graph
from rdflib.compare import IsomorphicGraph
from rdflib.namespace import RDF

from model.helpers import xsd_boolean
from model.helpers import xsd_datetime
from model.helpers import xsd_integer
from model.helpers import hex_rgb
from model.helpers import python_datetime_snowflake

from model.namespace import DISCORD
from model.namespace import DISCORDGUILD
from model.namespace import DISCORDROLE
from model.namespace import DISCORDUSER
from model.namespace import DISCORDPERMISSIONS


def simplify_uri(uri: str) -> str:
    """Removes query strings and other appendices from a URI."""
    return urljoin(uri, urlparse(uri).path)


def object_to_uri(value: object) -> URIRef:
    """Resolves the URI of an object, if possible."""
    if isinstance(value, Guild):
        return DISCORDGUILD[str(value.id)]
    elif isinstance(value, (Member, User, ClientUser)):
        return DISCORDUSER[str(value.id)]
    elif isinstance(value, Role):
        return DISCORDROLE[str(value.id)]
    elif isinstance(value, Attachment):
        return URIRef(simplify_uri(value.url))
    elif isinstance(value, (Message, GuildChannel)):
        return URIRef(simplify_uri(value.jump_url))
    raise TypeError(f"Unable to determine URI for {value}")


def object_to_graph(value: object) -> IsomorphicGraph:
    """Extracts triples from an object, based on the type."""
    uri = object_to_uri(value)
    triples = [(uri, RDF.type, DISCORD.Snowflake)]
    if isinstance(value, Guild):
        triples.extend(
            (
                (uri, RDF.type, DISCORD.Guild),
                (uri, DISCORD.name, Literal(value.name)),
                (uri, DISCORD.icon, URIRef(simplify_uri(value.icon.url))),
                (uri, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (uri, DISCORD.editedAt, xsd_datetime(value.created_at)),
            )
        )
    if isinstance(value, Role):
        triples.extend(
            (
                (uri, RDF.type, DISCORD.Role),
                (uri, DISCORD.name, Literal(value.name)),
                (uri, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (uri, DISCORD.editedAt, xsd_datetime(value.created_at)),
                (
                    uri,
                    DISCORD.colour,
                    hex_rgb(value.colour.r, value.colour.g, value.colour.b),
                ),
                *(
                    (uri, DISCORD.permission, DISCORDPERMISSIONS[name])
                    for name, granted in value.permissions
                    if granted
                ),
            )
        )
    if isinstance(value, (Member, User)):
        triples.extend(
            (
                (uri, RDF.type, DISCORD.User),
                (uri, DISCORD.name, Literal(value.name)),
                (uri, DISCORD.displayName, Literal(value.display_name)),
                (uri, DISCORD.displayAvatar, URIRef(value.display_avatar.url)),
                (uri, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (uri, DISCORD.editedAt, xsd_datetime(value.created_at)),
                (uri, DISCORD.bot, xsd_boolean(value.bot)),
                (uri, DISCORD.system, xsd_boolean(value.system)),
            )
        )
    if isinstance(value, Member):
        triples.extend((uri, DISCORD.role, object_to_uri(role)) for role in value.roles)
    if isinstance(value, Attachment):
        creation_date = python_datetime_snowflake(value.id)
        triples.extend(
            (
                (uri, RDF.type, DISCORD.Attachment),
                (uri, DISCORD.name, Literal(value.filename)),
                (uri, DISCORD.sizeBytes, xsd_integer(value.size)),
                (uri, DISCORD.createdAt, xsd_datetime(creation_date)),
                (uri, DISCORD.editedAt, xsd_datetime(creation_date)),
            )
        )
        if value.description:
            triples.append((uri, DISCORD.description, Literal(value.description)))
        if value.content_type:
            triples.append((uri, DISCORD.contentType, Literal(value.content_type)))
        if value.height:
            triples.append((uri, DISCORD.heightPixels, xsd_integer(value.height)))
        if value.width:
            triples.append((uri, DISCORD.widthPixels, xsd_integer(value.width)))
    if isinstance(value, Message):
        triples.extend(
            (
                (uri, RDF.type, DISCORD.Message),
                (uri, DISCORD.content, Literal(value.clean_content)),
                (uri, DISCORD.author, object_to_uri(value.author)),
                (uri, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (
                    uri,
                    DISCORD.editedAt,
                    xsd_datetime(value.edited_at or value.created_at),
                ),
                (uri, DISCORD.channel, object_to_uri(value.channel)),
                *(
                    (uri, DISCORD.attachment, object_to_uri(attachment))
                    for attachment in value.attachments
                ),
            )
        )
    if isinstance(value, GuildChannel):
        triples.extend(
            (
                (uri, RDF.type, DISCORD.Channel),
                (uri, DISCORD.name, Literal(value.name)),
                (uri, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (uri, DISCORD.editedAt, xsd_datetime(value.created_at)),
            )
        )
        if value.category:
            triples.extend(
                (
                    (uri, DISCORD.category, object_to_uri(value.category)),
                    (
                        uri,
                        DISCORD.permissionsSynced,
                        xsd_boolean(value.permissions_synced),
                    ),
                )
            )
        if isinstance(value, VoiceChannel):
            triples.extend(
                (
                    (uri, DISCORD.userLimit, xsd_integer(value.user_limit)),
                    (uri, DISCORD.bitRate, xsd_integer(value.bitrate)),
                    (
                        uri,
                        DISCORD.videoQualityMode,
                        Literal(value.video_quality_mode.name),
                    ),
                )
            )
            if value.rtc_region:
                triples.append((uri, DISCORD.rtcRegion, Literal(value.rtc_region)))
        if isinstance(value, TextChannel) and value.topic:
            triples.append((uri, DISCORD.description, Literal(value.topic)))
        if isinstance(value, (TextChannel, ForumChannel, VoiceChannel)):
            triples.append((uri, DISCORD.nsfw, xsd_boolean(value.nsfw)))
    graph = IsomorphicGraph(identifier=uri)
    for triple in triples:
        graph.add(triple)
    assert len(graph) > 1, f"Unable to convert {value} into graph"
    return graph


def get_edited_at(graph: Graph, uri: URIRef) -> datetime:
    """Gets the modification date of the item."""
    edited_at: Tuple[Literal] = tuple(
        graph.objects(subject=uri, predicate=DISCORD.editedAt)
    )
    edited_count = len(edited_at)
    assert edited_count == 1, f"Found {edited_count} edit dates for <{uri}>"
    edited_date: datetime = edited_at[0].toPython()
    assert edited_date.tzinfo, f"Timezone-unaware edit date on <{uri}>"
    return edited_date


def set_edited_at(graph: Graph, uri: URIRef, timestamp: datetime) -> None:
    """Sets the modification date of item to the specified datetime."""
    assert timestamp.tzinfo, "Modification time is timezone-unaware"
    graph.set((uri, DISCORD.editedAt, xsd_datetime(timestamp)))


def get_type_names(graph: Graph) -> Iterable[str]:
    """Gets the type names."""
    type_uris: Iterable[URIRef] = set(
        graph.objects(predicate=RDF.type, unique=True)
    ).difference((DISCORD.Snowflake,))
    type_names: List[str] = []
    for uri in type_uris:
        type_names.append(uri.removeprefix(DISCORD._NS).lower())
    return type_names


def graph_to_turtle(graph: Graph) -> str:
    """
    Converts the specified graph to Turtle format,
    taking care of the prefix bindings.
    """
    graph.bind("discord", DISCORD)
    turtle = graph.serialize(format="turtle")
    return turtle
