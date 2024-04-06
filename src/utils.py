from io import StringIO
from typing import Dict, Any
from difflib import unified_diff
from datetime import datetime
from discord.file import File
from discord.utils import utcnow
from discord.abc import GuildChannel
from discord.member import Member
from discord.message import Message

from src.config import DATE_FORMAT


def event_data(event: str, target: Message | GuildChannel | Member) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "event": {
            "type": event,
            "time": utcnow().strftime(DATE_FORMAT),
        },
    }
    if isinstance(target, Message):
        data["message"] = {
            "author": f"{target.author.display_name} {target.author.mention}",
            "channel": f"{target.channel.name} {target.channel.mention}",
            "attachments": len(target.attachments),
            "created": target.created_at.strftime(DATE_FORMAT),
            "reactions": len(target.reactions),
            "edited": (
                target.edited_at.strftime(DATE_FORMAT) if target.edited_at else None
            ),
        }
    elif isinstance(target, Member):
        data["member"] = {
            "identity": f"{target.display_name} {target.mention}",
            "registered": target.created_at.strftime(DATE_FORMAT),
            "joined": target.joined_at.strftime(DATE_FORMAT),
        }
    elif isinstance(target, GuildChannel):
        data["channel"] = {
            "category": target.category.name if target.category else None,
            "created": target.created_at.strftime(DATE_FORMAT),
            "identity": f"{target.name} {target.mention}",
        }
    return data


def diff_file(id: int, a: str, b: str, a_date: datetime, b_date: datetime) -> File:
    diff_content = "\n".join(
        unified_diff(
            a=a.splitlines(),
            b=b.splitlines(),
            fromfiledate=a_date.strftime(DATE_FORMAT),
            tofiledate=b_date.strftime(DATE_FORMAT),
            lineterm="",
        )
    )
    string_io = StringIO(initial_value=diff_content)
    diff_file = File(fp=string_io, filename=f"{id}.patch")
    return diff_file
