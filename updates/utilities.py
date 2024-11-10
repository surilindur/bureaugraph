from typing import Optional
from logging import debug
from logging import error
from logging import warning
from logging import exception

from yaml import dump

from discord.file import File
from discord.guild import Guild
from discord.errors import Forbidden

from graph.convert import uri


async def send_notification(guild: Guild, file: Optional[File]) -> None:
    """Sends a file to the public updates channel of the guild."""

    guild_uri = uri(guild)

    if not file:
        debug(f"Attempting to send an empty patch to <{guild_uri}>")
    elif not guild.public_updates_channel:
        warning(f"Missing updates channel in <{guild_uri}>")
    else:
        try:
            await guild.public_updates_channel.send(file=file)
            debug(f"Sent file to updates channel in <{guild_uri}>")
        except Forbidden:
            warning(f"Missing permissions for updates channel in <{guild_uri}>")
        except Exception as ex:
            error("Unable to send notification")
            exception(ex)
            await send_notification_failure(guild, file)


async def send_notification_failure(guild: Guild, file: Optional[File]) -> None:
    """Sends a message about notification failure to the updates channel."""

    metadata = {
        "error": "Failed to send update notification",
        "file": (
            {
                "bytes": file.__sizeof__(),
                "closed": file.fp.closed,
                "description": file.description,
                "filename": file.filename,
                "spoiler": file.spoiler,
            }
            if file
            else None
        ),
    }

    metadata_yaml = dump(metadata, indent=2, sort_keys=True, allow_unicode=True)

    try:
        await guild.public_updates_channel.send(f"```yaml\n{metadata_yaml}\n```")
    except Exception as ex:
        exception(ex)
