from datetime import UTC
from datetime import datetime
from urllib.parse import urlparse

from discord.abc import User
from discord.abc import GuildChannel
from discord.role import Role
from discord.guild import Guild
from discord.emoji import Emoji
from discord.member import Member
from discord.threads import Thread
from discord.channel import VocalGuildChannel
from discord.channel import TextChannel
from discord.channel import ForumChannel
from discord.sticker import GuildSticker
from discord.message import Attachment
from discord.message import Message
from discord.stage_instance import StageInstance
from discord.scheduled_events import ScheduledEvent

from rdflib.term import URIRef
from rdflib.term import Literal
from rdflib.compare import IsomorphicGraph
from rdflib.namespace import RDF
from rdflib.namespace import XSD

from graph.vocabulary import DISCORD
from graph.vocabulary import DISCORD_URI


def uri(value: object) -> URIRef:
    """Resolves the URI of an object, if possible."""
    if isinstance(value, str):
        parsed_url = urlparse(value)
        return URIRef(parsed_url.path, parsed_url.geturl())
    elif isinstance(value, (ScheduledEvent, Attachment)):
        parsed_url = urlparse(value.url)
        return URIRef(parsed_url.path, parsed_url.geturl())
    elif isinstance(value, User):
        return URIRef(f"{DISCORD_URI}/users/{value.id}")
    elif isinstance(value, Guild):
        return URIRef(f"{DISCORD_URI}/guilds/{value.id}")
    elif isinstance(value, (Role, GuildSticker, Emoji)):
        return URIRef(f"{DISCORD_URI}/guilds/{value.guild.id}/{value.id}")
    elif isinstance(value, StageInstance):
        return URIRef(
            f"{DISCORD_URI}/channels/{value.guild}/{value.channel_id}/{value.id}"
        )
    elif isinstance(value, (Message, GuildChannel, Thread)):
        return URIRef(value.jump_url)
    raise TypeError(f"Unable to determine URI for type {type(value)}")


def xsd_datetime(value: datetime) -> Literal:
    """Convert a Python datetime object into literal with datatype xsd:dateTime"""
    return Literal(
        lexical_or_value=value.isoformat(timespec="seconds"),
        datatype=XSD.dateTime,
    )


def xsd_integer(value: int) -> Literal:
    """Convert a Python integer value into literal with datatype xsd:integer"""
    return Literal(
        lexical_or_value=str(value),
        datatype=XSD.integer,
    )


def xsd_boolean(value: bool) -> Literal:
    """Convert a Python boolean value into string literal with datatype xsd:boolean"""
    return Literal(
        lexical_or_value=str(value).lower(),
        datatype=XSD.boolean,
    )


def snowflake_datetime(id: int) -> datetime:
    """
    Utility function to convert a Snowflake ID into a timezone-aware datetime.
    """
    return datetime.fromtimestamp(
        timestamp=((id >> 22) + 1288834974657) / 1000,
        tz=UTC,
    )


def python_datetime(value: str) -> datetime:
    """Utility function to parse an ISO 8601 datetime into Python object."""
    return datetime.fromisoformat(value).astimezone(UTC)


def iso_datetime(value: datetime) -> str:
    """
    Utility function to convert python datetime objects into string.
    The strings will follow the ISO format, without milliseconds or microseconds.
    This function exists to avoid manual repetition of the timespec argument.
    """
    assert value.tzinfo, f"Timezone-unaware datetime object: {value}"
    return value.isoformat(timespec="seconds")


def hex_rgb(red: int, green: int, blue: int) -> Literal:
    """Utility function to convert an RGB value into a hexadecimal string."""
    return Literal(f"#{red:02x}{green:02x}{blue:02x}")


def cbd(value: object) -> IsomorphicGraph:
    """Creates the Concise Bounded Description for a supported Python object."""
    graph = IsomorphicGraph(identifier=uri(value))
    graph.add((graph.identifier, RDF.type, DISCORD.Snowflake))
    if isinstance(value, Guild):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Guild),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.icon, uri(value.icon.url)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
        ):
            graph.add(triple)
    elif isinstance(value, Role):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Role),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
            (
                graph.identifier,
                DISCORD.colour,
                hex_rgb(value.colour.r, value.colour.g, value.colour.b),
            ),
            *(
                (graph.identifier, DISCORD.permission, Literal(name))
                for name, granted in value.permissions
                if granted
            ),
        ):
            graph.add(triple)
    elif isinstance(value, Emoji):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Emoji),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.managed, xsd_boolean(value.managed)),
            (graph.identifier, DISCORD.animated, xsd_boolean(value.animated)),
            *((graph.identifier, DISCORD.role, uri(role)) for role in value.roles),
        ):
            graph.add(triple)
    elif isinstance(value, GuildSticker):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.GuildSticker),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.emoji, Literal(value.emoji)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.description, Literal(value.description)),
            (
                graph.identifier,
                DISCORD.contentType,
                Literal(f"image/{value.format.name}"),
            ),
        ):
            graph.add(triple)
    elif isinstance(value, User):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.User),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.displayName, Literal(value.display_name)),
            (graph.identifier, DISCORD.bot, xsd_boolean(value.bot)),
        ):
            graph.add(triple)
        if value.avatar:
            graph.add((graph.identifier, DISCORD.avatar, uri(value.avatar.url)))
        if value.global_name:
            graph.add(
                (
                    graph.identifier,
                    DISCORD.globalName,
                    Literal(value.global_name),
                )
            )
        if isinstance(value, Member):
            for triple in (
                (
                    graph.identifier,
                    DISCORD.displayAvatar,
                    uri(value.display_avatar.url),
                ),
                (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
                (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
                (graph.identifier, DISCORD.system, xsd_boolean(value.system)),
                *((graph.identifier, DISCORD.role, uri(role)) for role in value.roles),
            ):
                graph.add(triple)
    elif isinstance(value, Attachment):
        creation_date = xsd_datetime(snowflake_datetime(value.id))
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Attachment),
            (graph.identifier, DISCORD.name, Literal(value.filename)),
            (graph.identifier, DISCORD.sizeBytes, xsd_integer(value.size)),
            (graph.identifier, DISCORD.createdAt, creation_date),
            (graph.identifier, DISCORD.editedAt, creation_date),
        ):
            graph.add(triple)
        if value.description:
            graph.add(
                (graph.identifier, DISCORD.description, Literal(value.description))
            )
        if value.content_type:
            graph.add(
                (graph.identifier, DISCORD.contentType, Literal(value.content_type))
            )
        if value.height:
            graph.add(
                (graph.identifier, DISCORD.heightPixels, xsd_integer(value.height))
            )
        if value.width:
            graph.add((graph.identifier, DISCORD.widthPixels, xsd_integer(value.width)))
    elif isinstance(value, Message):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Message),
            (graph.identifier, DISCORD.content, Literal(value.clean_content)),
            (graph.identifier, DISCORD.author, uri(value.author)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (
                graph.identifier,
                DISCORD.editedAt,
                xsd_datetime(value.edited_at or value.created_at),
            ),
            (graph.identifier, DISCORD.channel, uri(value.channel)),
            *(
                (graph.identifier, DISCORD.attachment, uri(attachment))
                for attachment in value.attachments
            ),
        ):
            graph.add(triple)
    elif isinstance(value, Thread):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Thread),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.archived, xsd_boolean(value.archived)),
        ):
            graph.add(triple)
        if value.archived:
            graph.add(
                (
                    graph.identifier,
                    DISCORD.archivedAt,
                    xsd_datetime(value.archive_timestamp),
                )
            )
        if value.parent:
            graph.add((graph.identifier, DISCORD.parent, uri(value.parent)))
    elif isinstance(value, GuildChannel):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.Channel),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.createdAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.editedAt, xsd_datetime(value.created_at)),
            (graph.identifier, DISCORD.channelType, Literal(value.type.name)),
        ):
            graph.add(triple)
        if value.category:
            graph.add((graph.identifier, DISCORD.category, uri(value.category)))
            graph.add(
                (
                    graph.identifier,
                    DISCORD.permissionsSynced,
                    xsd_boolean(value.permissions_synced),
                )
            )
        if isinstance(value, (TextChannel, VocalGuildChannel, ForumChannel)):
            graph.add((graph.identifier, DISCORD.nsfw, xsd_boolean(value.nsfw)))
        if isinstance(value, VocalGuildChannel):
            for triple in (
                (graph.identifier, DISCORD.userLimit, xsd_integer(value.user_limit)),
                (graph.identifier, DISCORD.bitRate, xsd_integer(value.bitrate)),
                (
                    graph.identifier,
                    DISCORD.videoQualityMode,
                    Literal(value.video_quality_mode.name),
                ),
            ):
                graph.add(triple)
            if value.rtc_region:
                graph.add(
                    (graph.identifier, DISCORD.rtcRegion, Literal(value.rtc_region))
                )
        elif isinstance(value, TextChannel) and value.topic:
            graph.add((graph.identifier, DISCORD.description, Literal(value.topic)))
    elif isinstance(value, ScheduledEvent):
        creation_date = xsd_datetime(value.created_at)
        for triple in (
            (graph.identifier, RDF.type, DISCORD.ScheduledEvent),
            (graph.identifier, DISCORD.name, Literal(value.name)),
            (graph.identifier, DISCORD.createdAt, creation_date),
            (graph.identifier, DISCORD.editedAt, creation_date),
            (graph.identifier, DISCORD.status, Literal(value.status.value)),
            (graph.identifier, DISCORD.startTime, xsd_datetime(value.start_time)),
            (graph.identifier, DISCORD.locationType, Literal(value.location.type.name)),
        ):
            graph.add(triple)
        if value.description:
            graph.add(
                (graph.identifier, DISCORD.description, Literal(value.description))
            )
        if value.end_time:
            graph.add((graph.identifier, DISCORD.endTime, xsd_datetime(value.end_time)))
    elif isinstance(value, StageInstance):
        for triple in (
            (graph.identifier, RDF.type, DISCORD.StageInstance),
            (graph.identifier, DISCORD.description, Literal(value.topic)),
            (
                graph.identifier,
                DISCORD.discoverableDisabled,
                xsd_boolean(value.discoverable_disabled),
            ),
            (graph.identifier, DISCORD.privacyLevel, Literal(value.privacy_level.name)),
        ):
            graph.add(triple)
    assert len(graph) > 1, f"Unable to convert {value} into graph"
    return graph
