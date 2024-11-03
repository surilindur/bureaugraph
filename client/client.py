from typing import Iterable
from random import choice
from logging import info
from logging import debug
from logging import error
from logging import warning
from logging import exception

from rdflib.graph import Graph

from discord import Intents
from discord.abc import GuildChannel
from discord.client import Client
from discord.ext.tasks import loop
from discord.file import File
from discord.role import Role
from discord.emoji import Emoji
from discord.utils import utcnow
from discord.guild import Guild
from discord.member import Member
from discord.sticker import GuildSticker
from discord.activity import CustomActivity
from discord.message import Message
from discord.raw_models import RawMemberRemoveEvent
from discord.raw_models import RawMessageUpdateEvent
from discord.raw_models import RawMessageDeleteEvent
from discord.raw_models import RawBulkMessageDeleteEvent

from client.constants import STATUS_STARTUP
from client.constants import STATUS_POOL
from client.reporting import get_diff
from client.commands import create_command_tree
from client.utilities import has_role
from client.utilities import message_uri_from_event
from client.utilities import message_uris_from_bulk_event
from client.utilities import message_attachment_uris
from client.utilities import event_metadata
from client.synctools import synchronise
from client.synctools import synchronise_guild
from client.synctools import synchronise_guilds
from client.synctools import synchronise_message
from client.synctools import synchronise_channels
from client.synctools import synchronise_channel_content
from client.storage import get_graph

from model.helpers import combined_cbd
from model.conversion import object_uri
from model.conversion import graph_to_turtle


class CustomClient(Client):
    def __init__(self, intents: Intents) -> None:
        super().__init__(intents=intents)
        self.initialisation_done: bool = False

    async def on_ready(self) -> None:
        try:
            info(f"Logged in as <{object_uri(self.user)}>")
            await self.update_status()
            info(f"Synchronising {len(self.guilds)} guild graphs with Discord state")
            await synchronise_guilds(self.guilds, sanitise=True, reset=False)
            self.command_tree = await create_command_tree(self)
            info("Synchronisation flow complete")
            self.initialisation_done = True
            self.refresh_status.start()
        except Exception as ex:
            exception(ex)
            info("Terminating self")
            await self.close()

    # Guild join and leave events

    async def on_guild_join(self, guild: Guild) -> None:
        """Handles the inclusion of a new guild in the graphs."""
        warning(f"Joined guild <{object_uri(guild)}>")
        await synchronise_guild(guild)

    async def on_guild_remove(self, guild: Guild) -> None:
        """Handles the removal of left guilds from the graphs."""
        guild_uri = object_uri(guild)
        warning(f"Left guild <{guild_uri}>")
        await synchronise_guild(guild_uri)

    # Message handling

    async def on_message(self, message: Message) -> None:
        if message.channel.id == message.guild.public_updates_channel.id:
            debug("Ignoring new message in updates channel")
        else:
            graph = get_graph(object_uri(message.guild))
            await synchronise_message(message, message.guild, graph)
            graph.commit()
            graph.close()

    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent) -> None:
        if not payload.guild_id:
            error("Ignoring message edit due to missing guild identifier")
        else:
            guild = self.get_guild(payload.guild_id)
            if payload.channel_id == guild.public_updates_channel.id:
                warning("Ignoring message edit in updates channel")
            else:
                channel = self.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                graph = get_graph(object_uri(guild))
                await synchronise_message(message, guild, graph)
                graph.commit()
                graph.close()

    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
        if not payload.guild_id:
            error("Ignoring delete due to missing guild identifier")
        else:
            guild = self.get_guild(payload.guild_id)
            if payload.channel_id == guild.public_updates_channel.id:
                warning("Ignoring message deletion in updates channel")
            else:
                graph = get_graph(object_uri(guild))
                message_uri = message_uri_from_event(payload)
                await synchronise_message(message_uri, guild, graph)
                graph.commit()
                graph.close()

    async def on_raw_bulk_message_delete(
        self,
        payload: RawBulkMessageDeleteEvent,
    ) -> None:
        if not payload.guild_id:
            error("Ignoring bulk delete due to missing guild identifier")
        else:
            guild = self.get_guild(payload.guild_id)
            if payload.channel_id == guild.public_updates_channel.id:
                warning("Ignoring message bulk deletion in updates channel")
            else:
                graph = get_graph(object_uri(guild))
                message_uris = message_uris_from_bulk_event(payload)
                attachment_uris = message_attachment_uris(graph, message_uris)
                deleted_cbds = combined_cbd(graph, message_uris + attachment_uris)
                graph -= deleted_cbds
                info(
                    "Bulk delete from <{}> (-{}, +0, ={})".format(
                        graph.identifier,
                        len(deleted_cbds),
                        len(graph),
                    )
                )
                diff_bytes = get_diff(
                    old=graph_to_turtle(deleted_cbds),
                    old_date=None,
                    new="",
                    new_date=utcnow(),
                    bytes=True,
                )
                await guild.public_updates_channel.send(
                    content=event_metadata(
                        event="bulk removed",
                        target_type="attachment, message, snowflake",
                        count=len(deleted_cbds),
                    ),
                    file=File(fp=diff_bytes, filename="graph.patch"),
                )
                graph.commit()
                graph.close()

    # Channel handling

    async def on_guild_channel_create(self, channel: GuildChannel) -> None:
        graph = get_graph(object_uri(channel.guild))
        await synchronise(channel, channel.guild, graph)
        graph.commit()
        graph.close()

    async def on_guild_channel_delete(self, channel: GuildChannel) -> None:
        graph = get_graph(object_uri(channel.guild))
        channel_uri = object_uri(channel)
        await synchronise(channel_uri, channel.guild, graph)
        await synchronise_channel_content(channel_uri, channel.guild, graph)
        graph.commit()
        graph.close()

    async def on_guild_channel_update(
        self,
        before: GuildChannel,
        after: GuildChannel,
    ) -> None:
        graph = get_graph(object_uri(after.guild))
        await synchronise(after, after.guild, graph)
        await synchronise_channel_content(after, after.guild, graph, silent=True)
        graph.commit()
        graph.close()

    # Role handling

    async def on_guild_role_create(self, role: Role) -> None:
        graph = get_graph(object_uri(role.guild))
        await synchronise(role, role.guild, graph)
        graph.commit()
        graph.close()

    async def on_guild_role_delete(self, role: Role) -> None:
        graph = get_graph(object_uri(role.guild))
        await synchronise(object_uri(role), role.guild, graph)
        graph.commit()
        graph.close()

    async def on_guild_role_update(self, before: Role, after: Role) -> None:
        remote_graph = get_graph(object_uri(after.guild))
        # Local temporary graph is needed because of the channel sync
        remote_graph_copy = Graph()
        remote_graph_copy += remote_graph
        local_graph = Graph()
        local_graph += remote_graph_copy
        await synchronise(after, after.guild, local_graph)
        if has_role(self.user, after):
            await synchronise_channels(local_graph, after.guild, silent=True)
        # Calculate the update for remote
        triples_added = local_graph - remote_graph_copy
        triples_removed = remote_graph_copy - local_graph
        # Update the remote graph based on local edits
        remote_graph -= triples_removed
        remote_graph += triples_added
        remote_graph.commit()
        remote_graph.close()

    # Member handling

    async def on_member_join(self, member: Member) -> None:
        graph = get_graph(object_uri(member.guild))
        await synchronise(member, member.guild, graph)
        graph.commit()
        graph.close()

    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent) -> None:
        guild = self.get_guild(payload.guild_id)
        graph = get_graph(object_uri(guild))
        await synchronise(object_uri(payload.user), guild, graph)
        graph.commit()
        graph.close()

    async def on_member_update(self, before: Member, after: Member) -> None:
        remote_graph = get_graph(object_uri(after.guild))
        # Local temporary graph is needed because of the channel sync
        remote_graph_copy = Graph()
        remote_graph_copy += remote_graph
        local_graph = Graph()
        local_graph += remote_graph_copy
        await synchronise(after, after.guild, local_graph)
        if before.id == self.user.id and before.roles != after.roles:
            await synchronise_channels(local_graph, after.guild, silent=True)
        # Calculate the update for remote
        triples_added = local_graph - remote_graph_copy
        triples_removed = remote_graph_copy - local_graph
        # Update the remote graph based on local edits
        remote_graph -= triples_removed
        remote_graph += triples_added
        remote_graph.commit()
        remote_graph.close()

    # Emoji handling

    async def on_guild_emojis_update(
        self,
        guild: Guild,
        before: Iterable[Emoji],
        after: Iterable[Emoji],
    ) -> None:
        graph = get_graph(object_uri(guild))
        before_map = {object_uri(e): e for e in before}
        after_map = {object_uri(e): e for e in after}
        for uri, emoji in before_map.items():
            if uri in after_map:
                emoji = after_map[uri]
                del after_map[uri]
            else:
                emoji = uri
            await synchronise(emoji, guild, graph)
        for uri, emoji in after_map.items():
            await synchronise(emoji, guild, graph)
        graph.commit()
        graph.close()

    # Sticker handling

    async def on_guild_stickers_update(
        self,
        guild: Guild,
        before: Iterable[GuildSticker],
        after: Iterable[GuildSticker],
    ) -> None:
        graph = get_graph(object_uri(guild))
        before_map = {object_uri(s): s for s in before}
        after_map = {object_uri(s): s for s in after}
        for uri, sticker in before_map.items():
            if uri in after_map:
                sticker = after_map[uri]
                del after_map[uri]
            else:
                sticker = uri
            await synchronise(sticker, guild, graph)
        for uri, sticker in after_map.items():
            await synchronise(sticker, guild, graph)
        graph.commit()
        graph.close()

    # Status message things

    @loop(hours=1)
    async def refresh_status(self) -> None:
        await self.update_status()

    async def update_status(self) -> None:
        debug("Updating user presence")
        status = choice(STATUS_POOL) if self.initialisation_done else STATUS_STARTUP
        await self.change_presence(activity=CustomActivity(name=status))
