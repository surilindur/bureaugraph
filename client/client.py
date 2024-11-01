from io import BytesIO
from enum import StrEnum
from json import dumps
from typing import Any
from typing import Dict
from typing import Iterable
from random import choice
from logging import info
from logging import debug
from logging import error
from logging import warning
from logging import exception
from traceback import format_exc

from yaml import dump

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
from discord.activity import CustomActivity
from discord.message import Message
from discord.channel import TextChannel
from discord.channel import ForumChannel
from discord.raw_models import RawMemberRemoveEvent
from discord.raw_models import RawMessageUpdateEvent
from discord.raw_models import RawMessageDeleteEvent
from discord.raw_models import RawBulkMessageDeleteEvent

from rdflib.term import URIRef
from rdflib.graph import Graph
from rdflib.compare import to_isomorphic
from rdflib.query import Result

from client.config import get_admin_user_id
from client.storage import get_store
from client.storage import get_guild_graph
from client.constants import STATUS_STARTUP
from client.constants import STATUS_POOL
from client.reporting import get_diff
from client.reporting import get_patches_from_graphs
from client.commands import create_command_tree

from model.namespace import DISCORD
from model.namespace import DISCORDCHANNELS
from model.conversion import get_type_names
from model.conversion import object_to_uri
from model.conversion import object_to_graph
from model.conversion import set_edited_at
from model.conversion import get_edited_at


class EventType(StrEnum):
    NONE = "noop"
    ADDED = "added"
    REMOVED = "removed"
    UPDATED = "updated"
    BULKREMOVED = "removed (bulk)"


class CustomClient(Client):
    initialisation_done: bool = False

    def __init__(self, intents: Intents) -> None:
        super().__init__(intents=intents)
        # The command tree holds all the slash command stuff
        self.tree = create_command_tree(client=self)

    async def on_ready(self) -> None:
        try:
            info(f"Logged in as <{object_to_uri(self.user)}>")
            await self.update_status()
            info(f"Synchronising {len(self.guilds)} guild graphs with Discord state")
            # await self.clear_graph()
            for guild in self.guilds:
                if guild.public_updates_channel:
                    await self.synchronise_guild(guild)
                    # Clear all the commands, and then sync the empty command tree
                    # self.tree.clear_commands(guild=guild)
                    self.tree.copy_global_to(guild=guild)
                    await self.tree.sync(guild=guild)
                else:
                    error(f"No updates channel in <{object_to_uri(guild)}>")
            info("Synchronisation flow complete")
            self.initialisation_done = True
            self.refresh_status.start()
        except Exception as ex:
            exception(ex)
            info("Terminating self")
            await self.close()

    async def on_error(self, event_method: str, *args: Any, **kwargs: Any) -> None:
        await super().on_error(event_method, *args, **kwargs)
        try:
            admin_uid = get_admin_user_id()
            user = self.get_user(admin_uid)
            if user:
                info(f"Sending error message to <{object_to_uri(user)}>")
                stacktrace_file = File(
                    fp=BytesIO(format_exc().encode()),
                    filename="stacktrace.log",
                )
                error_metadata = dumps(
                    {
                        "event_method": event_method,
                        "args": tuple(repr(a) for a in args),
                        "kwargs": dict({k: repr(v) for k, v in kwargs.items()}),
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    indent=2,
                )
                await user.send(
                    content=f"```json\n{error_metadata}\n```",
                    file=stacktrace_file,
                )
        except Exception as ex:
            exception(ex)

    async def clear_graph(self, uri: URIRef | None = None) -> None:
        """
        Completely erase all data in the remote store.
        Unless a graph URI is provided, all data will be purged.
        """
        if uri:
            warning(f"Clearing graph <{uri}>")
            graph = f"<{uri}>"
        else:
            warning(f"Clearing all stored graphs")
            graph = "?g"
        store = get_store()
        store.update(f"DELETE WHERE {{ GRAPH {graph} {{ ?s ?p ?o }} }}")
        result: Result = store.query(f"ASK WHERE {{ GRAPH {graph} {{ ?s ?p ?o }} }}")
        assert not result.askAnswer, f"Clearing failed, some triples were left"

    async def synchronise_guild(self, guild: Guild) -> None:
        """
        Synchronises local guild state with Discord state.
        This will go through the contents of the entire guild,
        and might be extremely slow for large servers.
        """
        start_time = utcnow()

        store_graph = get_guild_graph(guild)

        # Create a local working graph to speed up the process
        store_graph_copy = Graph()
        store_graph_copy += store_graph

        # Check if the current sync is the first one for a given guild
        previous_size = len(store_graph_copy)

        info(f"Syncing <{store_graph.identifier}> (previously {previous_size} triples)")

        # Working copy of the graph, that will be updated to reflect the changes
        local_graph = Graph()
        local_graph += store_graph_copy

        # Track the subject URIs discovered in Discord
        discord_subjects = set()

        # Helper function to avoid repetition
        async def synchronise_entity(entity: object) -> None:
            entity_uri = object_to_uri(entity)
            discord_subjects.add(entity_uri)
            await self.synchronise_cbd(
                uri=entity_uri,
                old_cbd=store_graph_copy.cbd(entity_uri),
                new_cbd=object_to_graph(entity),
                guild=guild,
                graph=local_graph,
                # Avoid spamming updates on initial guild sync pass
                verbose=previous_size > 0,
            )

        await synchronise_entity(guild)
        for role in guild.roles:
            await synchronise_entity(role)
        for member in guild.members:
            await synchronise_entity(member)
        for channel in guild.channels:
            if channel.id == guild.public_updates_channel.id:
                warning(f"Skipping <{object_to_uri(channel)}> as update channel")
            else:
                await synchronise_entity(channel)
                if isinstance(channel, (TextChannel, ForumChannel)):
                    async for message in channel.history(limit=None, oldest_first=True):
                        await synchronise_entity(message)
                        for attachment in message.attachments:
                            await synchronise_entity(attachment)

        # The subjects that could not be found on Discord, but that were in the graph,
        # have been deleted entirely, and should be reported as such.
        for subject in set(store_graph_copy.subjects(unique=True)).difference(
            discord_subjects
        ):
            await self.synchronise_cbd(
                uri=subject,
                old_cbd=store_graph_copy.cbd(subject),
                new_cbd=Graph(),  # Empty graph to indicate full deletion
                guild=guild,
                graph=local_graph,
            )

        removals = store_graph_copy - local_graph
        additions = local_graph - store_graph_copy

        if removals:
            store_graph -= removals

        if additions:
            store_graph += additions

        # The sizes should match, but it makes sense to verify
        local_size = len(local_graph)
        store_size = len(store_graph)
        assert (
            local_size == store_size
        ), f"Graph size mismatch: store {store_size}, local {local_size}"

        # Commit the changes
        store_graph.commit()

        # Close the graphs
        store_graph.close()
        local_graph.close()
        store_graph_copy.close()

        # Report the current guild graph as synced
        info(
            "Synced <{}> (-{}, +{}, ={}) in {:.1f} seconds".format(
                store_graph.identifier,
                len(removals),
                len(additions),
                store_size,
                (utcnow() - start_time).total_seconds(),
            )
        )

    async def synchronise_cbd(
        self,
        uri: URIRef,
        old_cbd: Graph,
        new_cbd: Graph,
        graph: Graph,
        guild: Guild,
        verbose: bool = True,
    ) -> None:
        """
        Evaluate the given entity, to determine whether it has been modified,
        and send an update event when relevant.
        """
        assert old_cbd or new_cbd, "Attempting to compare empty graphs"
        # Making them isomorphic for comparison use
        old_cbd = to_isomorphic(old_cbd)
        new_cbd = to_isomorphic(new_cbd)
        # During the initial sync, the edited_at dates for Discord data are set to creation date
        if old_cbd and new_cbd:
            set_edited_at(
                new_cbd,
                uri,
                max(
                    get_edited_at(old_cbd, uri),
                    get_edited_at(new_cbd, uri),
                ),
            )
        # Immediately terminate if the graph has not been modified
        if old_cbd == new_cbd:
            debug(f"Unmodified <{uri}>")
            return
        # Track removals and additions separately
        removals = Graph()
        additions = Graph()
        event = EventType.NONE
        if not old_cbd:
            event = EventType.ADDED
            additions = new_cbd
        elif not new_cbd:
            event = EventType.REMOVED
            removals = old_cbd
        else:
            event = EventType.UPDATED
            removals = old_cbd - new_cbd
            additions = new_cbd - old_cbd
        info(f"Sync: {event.value} <{uri}> (-{len(removals)}, +{len(additions)})")
        if removals:
            graph -= removals
        if additions:
            graph += additions
        if event is EventType.UPDATED:
            # Ensure the edited-at attribute is always up-to-date
            set_edited_at(graph, uri, utcnow())
        types = get_type_names(old_cbd + new_cbd)
        if verbose and "message" not in types and "attachment" not in types:
            await self.send_update(
                guild=guild,
                event=event,
                types=types,
                files=get_patches_from_graphs(uri=uri, old=old_cbd, new=new_cbd),
            )
        # Closing these just in case
        old_cbd.close()
        new_cbd.close()
        removals.close()
        additions.close()

    async def send_update(
        self,
        guild: Guild,
        event: EventType,
        types: Iterable[str],
        files: Iterable[File] | None,
        extra_data: Dict[str, Any] = {},
    ) -> None:
        """
        Send a message to the guild updates channel.
        This function is used to perform logging of update/delete events.
        """
        if guild.public_updates_channel:
            channel_uri = object_to_uri(guild.public_updates_channel)
            info(f"Sending update message to <{channel_uri}>")
            data = {
                "event": event.value,
                "target": ", ".join(types),
                **extra_data,
            }
            data_yaml = dump(data=data, sort_keys=True, indent=2, allow_unicode=True)
            await guild.public_updates_channel.send(
                content=f"```yaml\n{data_yaml}```",
                files=files,
            )
        else:
            error(f"No updates channel in <{object_to_uri(guild)}>")

    # Guild join and leave events

    async def on_guild_join(self, guild: Guild) -> None:
        """Handles the inclusion of a new guild in the graphs."""
        guild_uri = object_to_uri(guild)
        warning(f"Joined guild <{guild_uri}>")
        await self.synchronise_guild(guild)

    async def on_guild_remove(self, guild: Guild) -> None:
        """Handles the removal of left guilds from the graphs."""
        guild_uri = object_to_uri(guild)
        warning(f"Left guild <{guild_uri}>")
        await self.clear_graph(guild_uri)

    # Message handling

    async def on_message(self, message: Message) -> None:
        if message.channel.id == message.guild.public_updates_channel.id:
            debug("Ignoring new message in updates channel")
            return
        graph = get_guild_graph(message.guild)
        await self.synchronise_cbd(
            uri=object_to_uri(message),
            old_cbd=Graph(),
            new_cbd=object_to_graph(message),
            graph=graph,
            guild=message.guild,
        )
        for attachment in message.attachments:
            await self.synchronise_cbd(
                uri=object_to_uri(attachment),
                old_cbd=Graph(),
                new_cbd=object_to_graph(attachment),
                graph=graph,
                guild=message.guild,
            )
        graph.commit()
        graph.close()

    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent) -> None:
        if not payload.guild_id:
            error("Ignoring edit due to missing guild identifier")
            return
        # Fetch all the necessary data
        guild = self.get_guild(payload.guild_id)
        update_channel = guild.public_updates_channel
        if payload.channel_id == update_channel.id:
            warning(f"Ignoring edit in <{object_to_uri(update_channel)}>")
            return
        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        # Do the actual update
        graph = get_guild_graph(guild)
        message_uri = object_to_uri(message)
        # Check the previously existing attachments
        missing_attachment_uris = list(
            graph.objects(
                subject=message_uri,
                predicate=DISCORD.attachment,
                unique=True,
            )
        )
        await self.synchronise_cbd(
            uri=message_uri,
            old_cbd=graph.cbd(message_uri),
            new_cbd=object_to_graph(message),
            graph=graph,
            guild=guild,
        )
        # Update any attachments that still exist, but may have been edited
        for attachment in message.attachments:
            attachment_uri = object_to_uri(attachment)
            # This attachment still exists -> remove it from the set
            missing_attachment_uris.remove(attachment_uri)
            await self.synchronise_cbd(
                uri=attachment_uri,
                old_cbd=graph.cbd(attachment_uri),
                new_cbd=object_to_graph(attachment),
                graph=graph,
                guild=guild,
            )
        # For each attachment that was deleted, report them as such
        for attachment_uri in missing_attachment_uris:
            await self.synchronise_cbd(
                uri=attachment_uri,
                old_cbd=graph.cbd(attachment_uri),
                new_cbd=Graph(),
                graph=graph,
                guild=guild,
            )
        graph.commit()
        graph.close()

    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
        if not payload.guild_id:
            error("Ignoring delete due to missing guild identifier")
            return
        # Fetch the available data
        guild = self.get_guild(payload.guild_id)
        update_channel = guild.public_updates_channel
        if payload.channel_id == update_channel.id:
            warning(f"Ignoring delete in <{object_to_uri(update_channel)}>")
            return
        # Report the deleted data, by fetching it from the graph
        graph = get_guild_graph(guild)
        message_uri = self.message_uri_from_event(payload)
        attachment_uris = tuple(
            graph.objects(
                subject=message_uri,
                predicate=DISCORD.attachment,
                unique=True,
            )
        )
        await self.synchronise_cbd(
            uri=message_uri,
            old_cbd=graph.cbd(message_uri),
            new_cbd=Graph(),
            graph=graph,
            guild=guild,
        )
        for attachment_uri in attachment_uris:
            await self.synchronise_cbd(
                uri=attachment_uri,
                old_cbd=graph.cbd(attachment_uri),
                new_cbd=Graph(),
                graph=graph,
                guild=guild,
            )
        graph.commit()
        graph.close()

    async def on_raw_bulk_message_delete(
        self,
        payload: RawBulkMessageDeleteEvent,
    ) -> None:
        if not payload.guild_id:
            error("Ignoring bulk delete due to missing guild identifier")
            return
        guild = self.get_guild(payload.guild_id)
        update_channel = guild.public_updates_channel
        if payload.channel_id == update_channel.id:
            warning(f"Ignoring bulk delete in <{object_to_uri(update_channel)}>")
            return
        message_uris = []
        for message_id in payload.message_ids:
            payload.message_id = message_id
            message_uris.append(f"<{self.message_uri_from_event(payload)}>")
        message_uris_diff_bytes = get_diff(
            old="\n".join(message_uris),
            old_date=None,
            new="",
            new_date=utcnow(),
            bytes=True,
        )
        graph = get_guild_graph(guild)
        graph.update(
            f"""
            DELETE {{
                ?attachment ?ap ?ao .
                ?message ?mp ?mo .
            }}
            WHERE {{
                VALUES ?message {{ {" ".join(message_uris)} }}

                ?message ?mp ?mo .

                OPTIONAL {{
                    ?message <{DISCORD.attachment}> ?attachment .
                    ?attachment ?ap ?ao .
                }}
            }}
        """
        )
        await self.send_update(
            guild=guild,
            event=EventType.BULKREMOVED,
            types=("snowflake", "message"),
            files=(File(fp=message_uris_diff_bytes, filename="messageids.patch"),),
            extra_data={
                "count": len(payload.message_ids),
            },
        )
        graph.commit()
        graph.close()

    # Channel handling

    async def on_guild_channel_create(self, channel: GuildChannel) -> None:
        graph = get_guild_graph(channel.guild)
        await self.synchronise_cbd(
            uri=object_to_uri(channel),
            old_cbd=Graph(),
            new_cbd=object_to_graph(channel),
            graph=graph,
            guild=channel.guild,
        )
        graph.commit()
        graph.close()

    async def on_guild_channel_delete(self, channel: GuildChannel) -> None:
        graph = get_guild_graph(channel.guild)
        channel_uri = object_to_uri(channel)
        # First, delete all attachments in the channel
        info(f"Deleting all messages and attachments in <{channel_uri}>")
        graph.update(
            f"""
            DELETE {{
                ?attachment ?ap ?ao .
                ?message ?mp ?mo .
            }}
            WHERE {{
                ?message <{DISCORD.channel}> <{channel_uri}> .
                ?message ?mp ?mo .

                OPTIONAL {{
                    ?message <{DISCORD.attachment}> ?attachment .
                    ?attachment ?ap ?ao .
                }}
            }}
        """
        )
        await self.synchronise_cbd(
            uri=channel_uri,
            old_cbd=graph.cbd(channel_uri),
            new_cbd=Graph(),
            graph=graph,
            guild=channel.guild,
        )
        graph.commit()
        graph.close()

    async def on_guild_channel_update(
        self,
        before: GuildChannel,
        after: GuildChannel,
    ) -> None:
        channel_uri = object_to_uri(after)
        before_graph = object_to_graph(before)
        after_graph = object_to_graph(after)
        if before_graph == after_graph:
            debug(f"Skip update without edits for <{channel_uri}>")
            return
        graph = get_guild_graph(after.guild)
        await self.synchronise_cbd(
            uri=channel_uri,
            old_cbd=graph.cbd(channel_uri),
            new_cbd=after_graph,
            graph=graph,
            guild=after.guild,
        )
        graph.commit()
        graph.close()

    # Role handling

    async def on_guild_role_create(self, role: Role) -> None:
        graph = get_guild_graph(role.guild)
        await self.synchronise_cbd(
            uri=object_to_uri(role),
            old_cbd=Graph(),
            new_cbd=object_to_graph(role),
            graph=graph,
            guild=role.guild,
        )
        graph.commit()
        graph.close()

    async def on_guild_role_delete(self, role: Role) -> None:
        graph = get_guild_graph(role.guild)
        role_uri = object_to_uri(role)
        await self.synchronise_cbd(
            uri=role_uri,
            old_cbd=graph.cbd(role_uri),
            new_cbd=Graph(),
            graph=graph,
            guild=role.guild,
        )
        graph.commit()
        graph.close()

    async def on_guild_role_update(self, before: Role, after: Role) -> None:
        role_uri = object_to_uri(before)
        before_graph = object_to_graph(before)
        after_graph = object_to_graph(after)
        if before_graph == after_graph:
            debug(f"Skip update without edits for <{role_uri}>")
            return
        graph = get_guild_graph(before.guild)
        await self.synchronise_cbd(
            uri=role_uri,
            old_cbd=graph.cbd(role_uri),
            new_cbd=after_graph,
            graph=graph,
            guild=before.guild,
        )
        graph.commit()
        graph.close()

    # Member handling

    async def on_member_join(self, member: Member) -> None:
        graph = get_guild_graph(member.guild)
        await self.synchronise_cbd(
            uri=object_to_uri(member),
            old_cbd=Graph(),
            new_cbd=object_to_graph(member),
            graph=graph,
            guild=member.guild,
        )
        graph.commit()
        graph.close()

    async def on_raw_member_remove(self, payload: RawMemberRemoveEvent) -> None:
        guild = self.get_guild(payload.guild_id)
        member_uri = object_to_uri(payload.user)
        graph = get_guild_graph(guild)
        await self.synchronise_cbd(
            uri=member_uri,
            old_cbd=graph.cbd(member_uri),
            new_cbd=Graph(),
            graph=graph,
            guild=guild,
        )
        graph.commit()
        graph.close()

    async def on_member_update(self, before: Member, after: Member) -> None:
        member_uri = object_to_uri(before)
        before_graph = object_to_graph(before)
        after_graph = object_to_graph(after)
        if before_graph == after_graph:
            debug(f"Skip update without edits for <{member_uri}>")
            return
        graph = get_guild_graph(before.guild)
        await self.synchronise_cbd(
            uri=member_uri,
            old_cbd=graph.cbd(member_uri),
            new_cbd=object_to_graph(after),
            graph=graph,
            guild=before.guild,
        )
        graph.commit()
        graph.close()

    # Emoji handling

    async def on_guild_emojis_update(
        self,
        guild: Guild,
        before: Iterable[Emoji],
        after: Iterable[Emoji],
    ) -> None:
        graph = get_guild_graph(guild)
        # Assuming the URI remains the same
        before_map = {object_to_uri(e): e for e in before}
        after_map = {object_to_uri(e): e for e in after}
        for uri, emoji in before_map.items():
            if uri in after_map:
                new_cbd = object_to_graph(after_map[uri])
                del after_map[uri]
            else:
                new_cbd = Graph()
            if object_to_graph(emoji) == new_cbd:
                debug(f"Skip update without edits for <{uri}>")
            else:
                await self.synchronise_cbd(
                    uri=uri,
                    old_cbd=graph.cbd(uri),
                    new_cbd=new_cbd,
                    graph=graph,
                    guild=guild,
                )
        for uri, emoji in after_map.items():
            await self.synchronise_cbd(
                uri=uri,
                old_cbd=Graph(),
                new_cbd=object_to_graph(emoji),
                graph=graph,
                guild=guild,
            )

    # Status message things

    @loop(hours=1)
    async def refresh_status(self) -> None:
        await self.update_status()

    async def update_status(self) -> None:
        debug("Updating user presence")
        status = choice(STATUS_POOL) if self.initialisation_done else STATUS_STARTUP
        await self.change_presence(activity=CustomActivity(name=status))

    # Utilities

    def message_uri_from_event(
        self,
        event: RawBulkMessageDeleteEvent | RawMessageDeleteEvent,
    ) -> URIRef:
        """Constructs a message URI from an event."""
        assert event.guild_id, "Cannot construct a message URI without guild ID"
        return URIRef(
            f"{event.guild_id}/{event.channel_id}/{event.message_id}",
            DISCORDCHANNELS,
        )
