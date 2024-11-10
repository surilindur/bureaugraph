from rdflib.term import URIRef
from rdflib.graph import Graph

from discord.file import File
from discord.role import Role
from discord.member import Member
from discord.scheduled_events import ScheduledEvent

from graph.patch import patch
from graph.convert import cbd


async def update_entity(graph: Graph, entity: Member | Role | ScheduledEvent) -> File:
    """Updates the stored entity."""

    after = cbd(entity)
    before = graph.cbd(after.identifier)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file


async def delete_entity(graph: Graph, entity_uri: URIRef) -> File:
    """Deletes the stored entity."""

    after = Graph()
    before = graph.cbd(entity_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file
