from io import BytesIO
from typing import Tuple
from typing import Optional

from rdflib.graph import Graph

from discord.file import File

from graph.utilities import serialize


async def graph_to_yaml(
    graph: Graph,
    filename: str,
) -> Tuple[Optional[str], Optional[File]]:
    """Creates a YAML message string or a file attachment from a graph."""

    content = None
    file = None

    graph_turtle = await serialize(graph)
    extra_characters = len("```yaml\n\n```")

    if len(graph_turtle) + extra_characters > 2000:
        graph_turtle_io = BytesIO(graph_turtle.encode())
        file = File(graph_turtle_io, filename)
    else:
        content = f"```yaml\n{graph_turtle}\n```"

    return content, file
