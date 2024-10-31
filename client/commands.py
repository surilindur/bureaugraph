from yaml import dump

from rdflib.namespace import RDF

from discord.client import Client
from discord.interactions import Interaction
from discord.app_commands import CommandTree
from discord.app_commands import AppCommandContext
from discord.app_commands import AppInstallationType
from discord.app_commands import command

from client.storage import get_guild_graph

from model.namespace import DISCORD


@command(description="Collect simple statistics about the server")
async def statistics(interaction: Interaction) -> None:
    assert interaction.guild, "Cannot collect statistics outside a guild"
    graph = get_guild_graph(interaction.guild)
    result = {
        "messages": sum(
            1 for _ in graph.subjects(predicate=RDF.type, object=DISCORD.Message)
        ),
        "users": sum(
            1 for _ in graph.subjects(predicate=RDF.type, object=DISCORD.User)
        ),
        "channels": sum(
            1 for _ in graph.subjects(predicate=RDF.type, object=DISCORD.Channel)
        ),
    }
    result_yaml = dump(result, sort_keys=True, allow_unicode=True)
    await interaction.response.send_message(f"```yaml\n{result_yaml}\n```")


def create_command_tree(client: Client) -> CommandTree:
    tree = CommandTree(
        client=client,
        allowed_contexts=AppCommandContext(
            guild=True,
            dm_channel=False,
            private_channel=False,
        ),
        allowed_installs=AppInstallationType(
            guild=True,
            user=False,
        ),
    )
    tree.add_command(statistics)
    return tree
