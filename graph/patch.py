from io import BytesIO
from enum import StrEnum
from typing import Optional
from logging import info
from logging import debug
from difflib import unified_diff

from rdflib.graph import Graph
from rdflib.compare import to_isomorphic
from rdflib.namespace import RDF

from discord.file import File
from discord.utils import utcnow

from graph.convert import iso_datetime
from graph.convert import xsd_datetime
from graph.utilities import edited
from graph.utilities import serialize
from graph.vocabulary import DISCORD


class PatchResult(StrEnum):
    CREATE = "create"
    DELETE = "delete"
    UPDATE = "update"


async def graph_diff(before: Graph, after: Graph) -> str:
    """Creates a diff between two graphs."""

    before_string = await serialize(before)
    before_edited = await edited(before)

    after_string = await serialize(after)
    after_edited = await edited(after)

    diff_lines = unified_diff(
        a=before_string.splitlines(),
        b=after_string.splitlines(),
        fromfiledate=iso_datetime(before_edited) if before_edited else "",
        tofiledate=iso_datetime(after_edited) if after_edited else "",
        lineterm="",
    )

    return "\n".join(diff_lines)


async def patch(graph: Graph, before: Graph, after: Graph) -> Optional[File]:
    """Updates the graph by removing the old data and adding the new."""

    assert graph.identifier, "Graph patching requires a graph with identifier"

    # Ensure the graphs can actually be compared
    before = to_isomorphic(before)
    after = to_isomorphic(after)

    # Ensure the edit date is always assigned the latest value before comparison
    for subject in before.subjects(predicate=DISCORD.editedAt, unique=True):
        if (subject, DISCORD.editedAt, None) in after:
            before_edit = before.value(subject=subject, predicate=DISCORD.editedAt)
            after_edit = after.value(subject=subject, predicate=DISCORD.editedAt)
            after.set((subject, DISCORD.editedAt, max(before_edit, after_edit)))

    if before == after:
        info(f"Unmodified <{graph.identifier}>")
        return

    before_len = len(before)
    after_len = len(after)

    if not before_len:
        result = PatchResult.CREATE
    elif not after_len:
        result = PatchResult.DELETE
    else:
        result = PatchResult.UPDATE

    deleted_triples = before - after
    added_triples = after - before

    # Ensure the edit dates for all modified subjects are set to the current time
    if result == PatchResult.UPDATE:
        xsd_datetime_now = xsd_datetime(utcnow())
        edited_subjects = set(deleted_triples.subjects(unique=True))
        edited_subjects.update(added_triples.subjects(unique=True))
        for subject in edited_subjects.intersection(after.subjects(unique=True)):
            if (subject, RDF.type, DISCORD.Message) not in after:
                for triple in before.triples((subject, DISCORD.editedAt, None)):
                    deleted_triples.add(triple)
                added_triples.set((subject, DISCORD.editedAt, xsd_datetime_now))
                # The after timestamp needs to be updated for it to show in diff
                after.set((subject, DISCORD.editedAt, xsd_datetime_now))
            else:
                debug(f"Skip edit time update for message <{subject}>")

    deleted_len = len(deleted_triples)
    added_len = len(added_triples)

    assert before_len - deleted_len + added_len == after_len, "Sync result mismatch"

    graph -= deleted_triples
    graph += added_triples

    info(
        "Sync: {} <{}> (-{}, +{}, ={})".format(
            result.value,
            graph.identifier,
            deleted_len,
            added_len,
            after_len,
        )
    )

    diff_string = await graph_diff(before, after)
    diff_io = BytesIO(diff_string.encode())

    patch_file = File(diff_io, f"graph.patch")

    return patch_file
