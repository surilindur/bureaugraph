from typing import Sequence, List
from datetime import timedelta
from logging import info, error
from collections import deque
from discord.file import File
from discord.client import Client
from discord.guild import Guild
from discord.member import Member
from discord.channel import TextChannel
from discord.message import Message
from discord.errors import Forbidden
from discord.utils import utcnow

from src.config import DATE_FORMAT, HISTORY_LENGTH, HISTORY_WEEKS
from src.utils import message_diff, metadata_content


class Apparatus(Client):
    async def on_ready(self) -> None:
        info(f"Logged in as {self.user}")
        await self.populate_internal_caches()

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return
        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")

    async def on_message_delete(self, message: Message) -> None:
        await self.handle_message_delete(message)

    async def on_bulk_message_delete(self, messages: List[Message]) -> None:
        for message in messages:
            await self.handle_message_delete(message)

    async def handle_message_delete(self, message: Message) -> None:
        data = {
            "message": {
                "author": f"{message.author.display_name} {message.author.mention}",
                "channel": f"{message.channel.name} {message.channel.mention}",
                "attachments": len(message.attachments),
                "created": message.created_at.strftime(DATE_FORMAT),
                "reactions": len(message.reactions),
                "edited": (
                    message.edited_at.strftime(DATE_FORMAT)
                    if message.edited_at
                    else "never"
                ),
            }
        }
        files = [
            *await self.copy_attachments(message=message),
            message_diff(
                message_id=message.id,
                old_content=message.content,
                new_content="",
                old_date=message.edited_at or message.created_at,
                new_date=message.edited_at or message.created_at,
            ),
        ]
        await self.server_update(
            guild=message.guild,
            content=metadata_content(event="message_delete", data=data),
            files=files,
        )

    async def on_message_edit(self, before: Message, after: Message) -> None:
        data = {
            "message": {
                "author": f"{before.author.display_name} {before.author.mention}",
                "channel": f"{before.channel.name} {before.channel.mention}",
                "attachments": len(before.attachments),
                "created": before.created_at.strftime(DATE_FORMAT),
                "reactions": len(before.reactions),
                "edited": (
                    before.edited_at.strftime(DATE_FORMAT)
                    if before.edited_at
                    else "never"
                ),
            }
        }
        files = [
            message_diff(
                message_id=before.id,
                old_content=before.content if before is not after else "",
                new_content=after.content,
                old_date=before.edited_at or before.created_at,
                new_date=after.edited_at or after.created_at,
            )
        ]
        await self.server_update(
            guild=before.guild,
            content=metadata_content(event="message_edit", data=data),
            files=files,
        )

    async def on_member_join(self, member: Member) -> None:
        data = {
            "member": {
                "identity": f"{member.display_name} {member.mention}",
                "registered": member.created_at.strftime(DATE_FORMAT),
                "joined": member.joined_at.strftime(DATE_FORMAT),
            }
        }
        await self.server_update(
            guild=member.guild,
            content=metadata_content(event="member_join", data=data),
        )

    async def on_member_remove(self, member: Member) -> None:
        data = {
            "member": {
                "identity": f"{member.display_name} {member.mention}",
                "registered": member.created_at.strftime(DATE_FORMAT),
                "joined": member.joined_at.strftime(DATE_FORMAT),
            }
        }
        await self.server_update(
            guild=member.guild,
            content=metadata_content(event="member_remove", data=data),
        )

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
            "member": {
                "identity": f"{before.display_name} {before.mention}",
                "registered": before.created_at.strftime(DATE_FORMAT),
                "joined": before.joined_at.strftime(DATE_FORMAT),
            },
            "updates": updates,
        }
        await self.server_update(
            guild=before.guild,
            content=metadata_content(event="member_update", data=data),
        )

    async def server_update(self, guild: Guild | None, **kwargs) -> None:
        if guild and guild.public_updates_channel:
            await guild.public_updates_channel.send(**kwargs)
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
