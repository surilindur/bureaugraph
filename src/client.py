from typing import Sequence, List
from datetime import timedelta
from logging import info, error
from collections import deque
from discord.file import File
from discord.client import Client
from discord.guild import Guild
from discord.channel import TextChannel
from discord.message import Message
from discord.errors import Forbidden
from discord.utils import utcnow

from src.config import DATE_FORMAT, HISTORY_LENGTH, HISTORY_WEEKS
from src.utils import message_diff, metadata_content


class App(Client):
    async def on_ready(self) -> None:
        info(f"Logged in as {self.user}")
        await self.populate_message_cache()

    async def on_message(self, message: Message) -> None:
        if message.author == self.user:
            return
        if message.content.startswith("$hello"):
            await message.channel.send("Hello!")

    async def on_message_delete(self, message: Message) -> None:
        data = {
            "author": f"{message.author.display_name} {message.author.mention}",
            "channel": f"{message.channel.name} {message.channel.mention}",
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
            "author": f"{before.author.display_name} {before.author.mention}",
            "channel": f"{before.channel.name} {before.channel.mention}",
        }
        if before is after:
            data["notes"] = "previous message content unavailable"
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

    async def server_update(self, guild: Guild | None, **kwargs) -> None:
        if guild and guild.public_updates_channel:
            await guild.public_updates_channel.send(**kwargs)
        else:
            error("Attempting to log a message without guild or update channel")

    async def populate_message_cache(self) -> None:
        after = utcnow() - timedelta(weeks=HISTORY_WEEKS)
        limit = HISTORY_LENGTH
        messages: List[Message] = []
        info(f"Loading old messages for {len(self.guilds)} servers")
        info(f"Maximum of {limit} per channel since {after.strftime(DATE_FORMAT)}")
        for guild in self.guilds:
            info(
                f"Processing {guild.name} <{guild.id}> with {len(guild.channels)} channels"
            )
            for channel in guild.channels:
                if channel is not guild.public_updates_channel and isinstance(
                    channel, TextChannel
                ):
                    try:
                        async for message in channel.history(
                            limit=limit,
                            after=after,
                            oldest_first=False,
                        ):
                            messages.append(message)
                    except Forbidden:
                        pass
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
