from io import BytesIO
from typing import Iterable
from pathlib import Path
from difflib import unified_diff
from datetime import datetime

from discord.utils import utcnow
from discord.file import File

from rdflib.term import URIRef
from rdflib.graph import Graph
from rdflib.namespace import RDF

from model.helpers import iso_datetime
from model.namespace import DISCORD
from model.conversion import get_edited_at


def count_subjects(graph: Graph) -> int:
    """Count the number of unique subjects in a graph."""
    return sum(1 for _ in graph.subjects(unique=True))


def bind_namespaces(graph: Graph) -> Graph:
    """Bind the custom namespaces to a graph."""
    graph.bind("discord", DISCORD)
    return graph


def get_diff(
    old: str,
    old_date: datetime | None,
    new: str,
    new_date: datetime,
    bytes: bool = False,
) -> str | BytesIO:
    """Generates a unified diff from two strings."""
    diff_lines = unified_diff(
        a=old.splitlines(),
        b=new.splitlines(),
        fromfiledate=iso_datetime(old_date) if old_date else "",
        tofiledate=iso_datetime(new_date),
        lineterm="",
    )
    diff_string = "\n".join(diff_lines)
    return BytesIO(initial_bytes=diff_string.encode()) if bytes else diff_string


def get_patches_from_graphs(
    uri: URIRef,
    old: Graph,
    new: Graph,
) -> Iterable[File]:
    """
    Generates a patch file from two sets of triples.
    This patch file can be included in a Discord message as attachment.
    """
    old_date = get_edited_at(old, uri) if old else None
    new_date = get_edited_at(new, uri) if new else utcnow()
    graph_diff_bytes = get_diff(
        old=bind_namespaces(old).serialize(format="turtle"),
        old_date=old_date,
        new=bind_namespaces(new).serialize(format="turtle"),
        new_date=new_date,
        bytes=True,
    )
    files = [File(fp=graph_diff_bytes, filename="graph.patch")]
    if (uri, RDF.type, DISCORD.Message) in old:
        old_content = tuple(old.objects(subject=uri, predicate=DISCORD.content))
        new_content = tuple(new.objects(subject=uri, predicate=DISCORD.content))
        assert (
            len(old_content) < 2 and len(new_content) < 2
        ), f"Too many content declarations for <{uri}>"
        old_content_string = old_content[0] if old_content else ""
        new_content_string = new_content[0] if new_content else ""
        if (
            old_content_string or new_content_string
        ) and old_content_string != new_content_string:
            content_diff_bytes = get_diff(
                old=old_content_string,
                old_date=old_date,
                new=new_content_string,
                new_date=new_date,
                bytes=True,
            )
            files.append(File(fp=content_diff_bytes, filename="content.patch"))
    return files


def serialize_to_file(graph: Graph, path: Path | str) -> None:
    """Serialize a graph to file as turtle."""
    with open(path, "wb") as graph_file:
        bind_namespaces(graph).serialize(
            destination=graph_file,
            format="turtle",
            encoding="utf-8",
        )
