from typing import Iterable

from rdflib.graph import Graph
from rdflib.namespace import RDF

from discord.file import File
from discord.emoji import Emoji

from graph.patch import patch
from graph.convert import cbd
from graph.vocabulary import DISCORD


async def update_emojis(graph: Graph, emojis: Iterable[Emoji]) -> File:
    """Updates the stored emojis."""

    before = Graph()
    after = Graph()

    emoji_uris = set(
        graph.subjects(
            predicate=RDF.type,
            object=DISCORD.Emoji,
            unique=True,
        )
    )

    for emoji in emojis:
        emoji_cbd = cbd(emoji)
        after += emoji_cbd
        before += graph.cbd(emoji_cbd.identifier)
        if emoji_cbd.identifier in emoji_uris:
            emoji_uris.remove(emoji_cbd.identifier)

    for emoji_uri in emoji_uris:
        before += graph.cbd(emoji_uri)

    file = await patch(graph, before, after)

    after.close()
    before.close()

    return file
