from io import StringIO
from yaml import dump
from typing import Dict
from difflib import unified_diff
from datetime import datetime
from discord.file import File
from discord.utils import utcnow

from src.config import DATE_FORMAT


def metadata_content(event: str, data: Dict[str, str | int | float]) -> str:
    data = {
        **data,
        "event": event,
        "time": utcnow().strftime(DATE_FORMAT),
    }
    content = f"```yaml\n{dump(data=data, allow_unicode=True)}```"
    return content


def file_from_string(filename: str, content: str) -> File:
    fp = StringIO(content)
    file = File(fp=fp, filename=filename)
    return file


def message_diff(
    message_id: int,
    old_content: str,
    new_content: str,
    old_date: datetime,
    new_date: datetime,
) -> File:
    content = "\n".join(
        unified_diff(
            a=old_content.splitlines(),
            b=new_content.splitlines(),
            fromfiledate=(old_date).strftime(DATE_FORMAT),
            tofiledate=(new_date).strftime(DATE_FORMAT),
            lineterm="",
        )
    )
    return file_from_string(filename=f"{message_id}.patch", content=content)
