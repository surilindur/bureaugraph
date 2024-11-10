from typing import Iterable

from rdflib.graph import Graph
from rdflib.namespace import RDF

from discord.file import File
from discord.sticker import GuildSticker

from graph.patch import patch
from graph.convert import cbd
from graph.vocabulary import DISCORD


async def update_guild_stickers(graph: Graph, stickers: Iterable[GuildSticker]) -> File:
    """Updates the stored guild stickers."""

    before = Graph()
    after = Graph()

    sticker_uris = set(
        graph.subjects(
            predicate=RDF.type,
            object=DISCORD.GuildSticker,
            unique=True,
        )
    )

    for sticker in stickers:
        sticker_cbd = cbd(sticker)
        after += sticker_cbd
        before += graph.cbd(sticker_cbd.identifier)
        if sticker_cbd.identifier in sticker_uris:
            sticker_uris.remove(sticker_cbd.identifier)

    for sticker_uri in sticker_uris:
        before += graph.cbd(sticker_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file
