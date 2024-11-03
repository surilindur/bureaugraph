from io import BytesIO
from typing import Iterable
from difflib import unified_diff
from datetime import datetime

from discord.utils import utcnow
from discord.file import File

from rdflib.graph import Graph

from client.utilities import latest_edited_at

from model.helpers import iso_datetime
from model.namespace import DISCORD
from model.conversion import graph_to_turtle


def get_diff(
    old: str,
    old_date: datetime | None,
    new: str,
    new_date: datetime,
) -> str:
    """Generates a unified diff from two strings."""
    return "\n".join(
        unified_diff(
            a=old.splitlines(),
            b=new.splitlines(),
            fromfiledate=iso_datetime(old_date) if old_date else "",
            tofiledate=iso_datetime(new_date),
            lineterm="",
        )
    )


def get_diff_bytes(
    old: str,
    old_date: datetime | None,
    new: str,
    new_date: datetime,
) -> BytesIO:
    """Generates a unified diff from two strings as BytesIO."""
    return BytesIO(get_diff(old, old_date, new, new_date).encode())


def get_patch(old: Graph, new: Graph, filename: str) -> File:
    """Generates a Discord File object with the patch between two graphs."""
    diff_bytesio = get_diff_bytes(
        old=graph_to_turtle(old),
        old_date=latest_edited_at(old),
        new=graph_to_turtle(new),
        new_date=latest_edited_at(new) or utcnow(),
    )
    return File(fp=diff_bytesio, filename=filename)


def get_patches_for_notification(old: Graph, new: Graph) -> Iterable[File]:
    """Generates all patches to be attached to an update notification."""
    files = [get_patch(old, new, "graph.patch")]
    utc_now = utcnow()
    old_content = {
        uri: content
        for uri, content in old.subject_objects(
            predicate=DISCORD.content,
            unique=True,
        )
    }
    old_cbds = {uri: old.cbd(uri) for uri in old_content.keys()}
    new_content = {
        uri: content
        for uri, content in new.subject_objects(
            predicate=DISCORD.content,
            unique=True,
        )
    }
    new_cbds = {uri: new.cbd(uri) for uri in new_content.keys()}
    for uri, content in old_content.items():
        if uri in new_content:
            new = new_content[uri]
            new_date = latest_edited_at(new_cbds[uri]) or utc_now
            del new_content[uri]
            del new_cbds[uri]
        else:
            new = ""
            new_date = utc_now
        if content != new:
            diff_bytesio = get_diff_bytes(
                old=content,
                old_date=latest_edited_at(old_cbds[uri]),
                new=new,
                new_date=new_date,
            )
            file = File(fp=diff_bytesio, filename="content.patch")
            files.append(file)
    for uri, content in new_content.items():
        if content != "":
            diff_bytesio = get_diff_bytes(
                old="",
                old_date=None,
                new=content,
                new_date=latest_edited_at(new_cbds[uri]) or utc_now,
            )
            file = File(fp=diff_bytesio, filename="content.patch")
            files.append(file)
    return files
