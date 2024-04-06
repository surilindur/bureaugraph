from typing import Sequence, List, Dict, Any
from datetime import timedelta
from logging import info, error
from collections import deque
from yaml import dump
from discord.abc import GuildChannel
from discord.file import File
from discord.client import Client
from discord.guild import Guild
from discord.member import Member
from discord.channel import TextChannel
from discord.message import Message
from discord.errors import Forbidden
from discord.utils import utcnow

from src.config import DATE_FORMAT, HISTORY_LENGTH, HISTORY_WEEKS
from src.utils import event_data, diff_file


class Apparatus(Client):
    async def on_ready(self) -> None:
        info(f"Logged in as {self.user}")
        await self.populate_internal_caches()

    async def on_message_delete(self, message: Message) -> None:
        await self.handle_message_delete(message)

    async def on_bulk_message_delete(self, messages: List[Message]) -> None:
        for message in messages:
            await self.handle_message_delete(message)

    async def handle_message_delete(self, message: Message) -> None:
        data = event_data(event="message_delete", target=message)
        files = [
            *await self.copy_attachments(message=message),
            diff_file(
                id=message.id,
                a=message.content,
                b="",
                a_date=message.edited_at or message.created_at,
                b_date=message.edited_at or message.created_at,
            ),
        ]
        await self.record_event(guild=message.guild, data=data, files=files)

    async def on_message_edit(self, before: Message, after: Message) -> None:
        data = event_data(event="message_edit", target=before)
        files = [
            diff_file(
                id=before.id,
                a=before.content,
                b=after.content,
                a_date=before.edited_at or before.created_at,
                b_date=after.edited_at or after.created_at,
            )
        ]
        await self.record_event(guild=before.guild, data=data, files=files)

    async def on_member_join(self, member: Member) -> None:
        data = event_data(event="member_join", target=member)
        await self.record_event(guild=member.guild, data=data)

    async def on_member_remove(self, member: Member) -> None:
        data = event_data(event="member_remove", target=member)
        await self.record_event(guild=member.guild, data=data)

    async def on_member_update(self, before: Member, after: Member) -> None:
        updates = {}
        if after.display_name != before.display_name:
            updates["name_changed"] = f"{before.display_name} -> {after.display_name}"
        roles_added = set(after.roles).difference(before.roles)
        roles_removed = set(before.roles).difference(after.roles)
        if roles_added:
            updates["roles_added"] = (
                ",".join(r.name for r in roles_added) if roles_added else ""
            )
        if roles_removed:
            updates["roles_removed"] = (
                ",".join(r.name for r in roles_removed) if roles_removed else ""
            )
        data = {
            **event_data(event="member_update", target=before),
            "updates": updates,
        }
        await self.record_event(guild=before.guild, data=data)

    async def on_guild_channel_create(self, channel: GuildChannel) -> None:
        data = event_data(event="guild_channel_create", target=channel)
        await self.record_event(guild=channel.guild, data=data)

    async def on_guild_channel_delete(self, channel: GuildChannel) -> None:
        data = event_data(event="guild_channel_delete", target=channel)
        await self.record_event(guild=channel.guild, data=data)

    # async def on_guild_channel_update(
    #     self,
    #     before: GuildChannel,
    #     after: GuildChannel,
    # ) -> None:
    #     updates = {}
    #     if after.name != before.name:
    #         updates["name"] = f"{before.name} -> {after.name}"
    #     if after.category_id != before.category_id:
    #         updates["category"] = f"{before.category.name} -> {after.category.name}"
    #     data = {
    #         "channel": {
    #             "category": before.category.name if before.category else None,
    #             "created": before.created_at.strftime(DATE_FORMAT),
    #             "identity": f"{before.name} {before.mention}",
    #         },
    #         "updates": updates if len(updates) else "other",
    #     }
    #     await self.server_update(
    #         guild=before.guild,
    #         content=metadata_content(event="guild_channel_update", data=data),
    #     )

    async def record_event(
        self,
        guild: Guild,
        data: Dict[str, Any],
        files: Sequence[File] = [],
    ) -> None:
        if guild.public_updates_channel:
            await guild.public_updates_channel.send(
                content=f"```yaml\n{dump(data=data, allow_unicode=True)}```",
                files=files,
            )
        else:
            error("Attempting to log a message without guild or update channel")

    async def populate_internal_caches(self) -> None:
        after = (utcnow() - timedelta(weeks=HISTORY_WEEKS)) if HISTORY_WEEKS else None
        messages: List[Message] = []
        history_length = HISTORY_LENGTH or "unlimited"
        after_string = after.strftime(DATE_FORMAT) if after else "the beginning"
        info(f"Loading old messages for {len(self.guilds)} servers")
        info(f"Maximum {history_length}/channel since {after_string}")
        for guild in self.guilds:
            info(f"Caching server {guild.name} <{guild.id}>")
            message_count = 0
            channel_count = 0
            for channel in guild.channels:
                if channel is not guild.public_updates_channel and isinstance(
                    channel, TextChannel
                ):
                    try:
                        async for message in channel.history(
                            limit=HISTORY_LENGTH,
                            after=after,
                            oldest_first=False,
                        ):
                            message_count += 1
                            messages.append(message)
                        channel_count += 1
                    except Forbidden:
                        pass
            info(f"Cached {message_count} messages from {channel_count} channels")
            async for member in guild.fetch_members(limit=None):
                guild._members[member.id] = member
            info(f"Cached {len(guild._members)} members")
            for channel in await guild.fetch_channels():
                guild._channels[channel.id] = channel
            info(f"Cached {len(guild._channels)} channels")
        messages.sort(key=lambda m: m.edited_at or m.created_at)
        messages_length = len(messages)
        info(f"Loaded {messages_length} messages in total")
        cache_size = max(messages_length, self._connection._messages.maxlen)
        self._connection._messages = deque(messages, cache_size)
        info(f"Message cache has {self._connection._messages.maxlen} entries")

    async def copy_attachments(self, message: Message) -> Sequence[File]:
        files: Sequence[File] = []
        for attachment in message.attachments:
            try:
                file = await attachment.to_file(
                    filename=attachment.filename,
                    description=attachment.description,
                    use_cached=True,
                )
                files.append(file)
            except Exception as ex:
                error(ex)
        return files
