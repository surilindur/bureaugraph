from re import compile
from typing import Dict
from typing import Optional
from string import punctuation
from string import whitespace

from rdflib.term import BNode
from rdflib.term import Literal
from rdflib.term import Variable
from rdflib.graph import Graph
from rdflib.namespace import RDF
from rdflib.namespace import XSD
from rdflib.namespace import SDO

from discord.utils import utcnow
from discord.commands import option
from discord.commands import guild_only
from discord.ext.commands import cooldown
from discord.ext.commands import BucketType
from discord.commands.context import ApplicationContext

from client.bot import bot
from graph.convert import uri
from graph.convert import xsd_datetime
from graph.convert import xsd_integer
from graph.convert import iso_datetime
from graph.convert import python_datetime
from graph.storage import graph
from graph.utilities import parse_discord_uri
from graph.vocabulary import DISCORD
from commands.utilities import graph_to_yaml

STRIP_CHARACTERS = punctuation + whitespace
TOKENIZER_PATTERN = compile(r"(?P<token>\s+|\S+)")


@bot.slash_command(
    name="stc",
    description="Count the occurrences of various string tokens in messages",
)
@option(
    name="user",
    input_type=str,
    required=False,
    description="The URI of the user whose messages to consider",
)
@option(
    name="channel",
    input_type=str,
    required=False,
    description="The URI of the channel whose messages to consider",
)
@option(
    name="after",
    input_type=str,
    required=False,
    description="Consider messages sent after this timestamp, in ISO 8601 format",
)
@option(
    name="before",
    input_type=str,
    required=False,
    description="Consider messages sent before this timestamp, in ISO 8601 format",
)
@cooldown(rate=1, per=1, type=BucketType.user)
@guild_only()
async def command_stc(
    context: ApplicationContext,
    user: Optional[str],
    channel: Optional[str],
    after: Optional[str],
    before: Optional[str],
) -> None:

    # Parse the parameters
    guild_uri = uri(context.guild)
    user_uri = await parse_discord_uri(user) if user else None
    channel_uri = await parse_discord_uri(channel) if channel else None
    after_datetime = python_datetime(after) if after else None
    before_datetime = python_datetime(before) if before else None

    user_pattern = f"?message <{DISCORD.author}> <{user_uri}> ." if user_uri else ""

    created_pattern = (
        f"?message <{DISCORD.createdAt}> ?created ."
        if before_datetime or after_datetime
        else ""
    )

    channel_pattern = (
        f"?message <{DISCORD.channel}> | <{DISCORD.parent}> <{channel_uri}> ."
        if channel_uri
        else ""
    )

    filters = []

    if after_datetime:
        filters.append(f'?created > "{iso_datetime(after_datetime)}"^^<{XSD.dateTime}>')

    if before_datetime:
        filters.append(
            f'?created < "{iso_datetime(before_datetime)}"^^<{XSD.dateTime}>'
        )

    filters_string = f"FILTER ( {" && ".join(filters)} )" if filters else ""

    guild_graph = await graph(guild_uri)

    query_string = f"""
        SELECT
            ?content
        WHERE {{
            ?message <{RDF.type}> <{DISCORD.Message}> .
            {channel_pattern}
            {user_pattern}
            {created_pattern}
            ?message <{DISCORD.content}> ?content .

            {filters_string}
        }}
    """

    result = guild_graph.query(query_string)

    token_counts: Dict[str, int] = {}
    var_content = Variable("content")

    for bindings in result.bindings:
        content: str = bindings.get(var_content)
        for token in TOKENIZER_PATTERN.finditer(content):
            token = token.group("token").lower().strip(STRIP_CHARACTERS)
            if token in token_counts:
                token_counts[token] += 1
            elif not token.isnumeric() and token.isalnum():
                token_counts[token] = 1

    token_graph = Graph(identifier=BNode())

    for triple in (
        (token_graph.identifier, RDF.type, SDO.Dataset),
        (
            token_graph.identifier,
            SDO.measurementTechnique,
            Literal("string token counting"),
        ),
        (token_graph.identifier, SDO.dateCreated, xsd_datetime(utcnow())),
        (token_graph.identifier, SDO.sourceOrganization, guild_uri),
    ):
        token_graph.add(triple)

    for key, value in token_counts.items():
        token_observation = BNode()
        for triple in (
            (token_observation, RDF.type, SDO.Observation),
            (token_observation, SDO.value, xsd_integer(value)),
            (token_observation, SDO.measuredValue, Literal(key)),
            (token_graph.identifier, SDO.hasPart, token_observation),
        ):
            token_graph.add(triple)

    content, file = graph_to_yaml(token_graph, "stc.yaml")

    await context.respond(file=file)
