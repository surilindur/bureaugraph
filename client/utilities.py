from typing import Iterable
from datetime import datetime

from yaml import dump

from rdflib.term import URIRef
from rdflib.graph import Graph

from discord.abc import GuildChannel
from discord.user import User
from discord.user import ClientUser
from discord.role import Role
from discord.member import Member
from discord.channel import VoiceChannel
from discord.channel import TextChannel
from discord.channel import ForumChannel
from discord.raw_models import RawMessageDeleteEvent
from discord.raw_models import RawBulkMessageDeleteEvent

from model.namespace import DISCORD
from model.namespace import DISCORDCHANNELS


def can_access(user: Member | User | ClientUser, channel: GuildChannel) -> bool:
    """
    Check whether a user has sufficient access to a channel to be able to see it.
    For text channels, this requires message history read permissions.
    For voice channels, this requires connect permissions.
    """
    if isinstance(user, (User, ClientUser)):
        user = channel.guild.get_member(user.id)
    assert isinstance(user, Member), "Permission check requires a member"
    assert user.guild == channel.guild, "Permission check between different guilds"
    if isinstance(channel, (TextChannel, ForumChannel)):
        permissions = channel.permissions_for(user)
        return permissions.read_messages and permissions.read_message_history
    elif isinstance(channel, VoiceChannel):
        permissions = channel.permissions_for(user)
        return permissions.connect
    return False


def has_role(user: Member | User | ClientUser, role: Role) -> bool:
    """Check whether the specified user has the given role."""
    if isinstance(user, (User, ClientUser)):
        user = role.guild.get_member(user)
    assert isinstance(user, Member), "Role check requires a member"
    return role in user.roles


def latest_edited_at(*graphs: Graph) -> datetime | None:
    """Finds the latest edited at timestamp from multiple graphs."""
    latest_edited = None
    for graph in graphs:
        for edited_literal in graph.objects(predicate=DISCORD.editedAt, unique=True):
            edited_datetime = datetime.fromisoformat(edited_literal)
            if not latest_edited or edited_datetime > latest_edited:
                latest_edited = edited_datetime
    return latest_edited


def message_uri_from_event(
    event: RawMessageDeleteEvent,
) -> URIRef:
    """Constructs a message URI from an event."""
    assert event.guild_id, "Cannot construct a message URI without guild ID"
    return URIRef(
        f"{event.guild_id}/{event.channel_id}/{event.message_id}",
        DISCORDCHANNELS,
    )


def message_uris_from_bulk_event(event: RawBulkMessageDeleteEvent) -> Iterable[URIRef]:
    """Constructs message URIs from a bulk event."""
    assert event.guild_id, "Cannot construct message URIs without guild ID"
    return (
        URIRef(
            f"{event.guild_id}/{event.channel_id}/{message_id}",
            DISCORDCHANNELS,
        )
        for message_id in event.message_ids
    )


def message_attachment_uris(
    graph: Graph,
    message_uris: Iterable[URIRef],
) -> Iterable[URIRef]:
    """Collects all the attachment URIs for the specified messages URIs"""
    return (
        URIRef(bindings.get("attachment"))
        for bindings in graph.query(
            f"""
                SELECT DISTINCT ?attachment WHERE {{
                    VALUES {{ {" ".join(f"<{u}>" for u in message_uris)} }}
                    ?message <{DISCORD.attachment}> ?attachment .
                }}
            """
        )
    )


def event_metadata(event: str, target_type: str, **kwargs) -> str:
    """Creates the event metadata YAML string from parameters."""
    metadata = {"event": event, "type": target_type, **kwargs}
    metadata_yaml = dump(metadata, allow_unicode=True, indent=2, sort_keys=True)
    return f"```yaml\n{metadata_yaml}\n```"
