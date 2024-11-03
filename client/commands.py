from io import BytesIO
from logging import exception

from rdflib.graph import Graph

from discord.role import Role
from discord.member import Member
from discord.file import File
from discord.client import Client
from discord.interactions import Interaction
from discord.app_commands import CommandTree
from discord.app_commands import AppCommandError
from discord.app_commands import AppCommandContext
from discord.app_commands import AppInstallationType
from discord.app_commands import command

from client.storage import get_graph

from model.conversion import object_uri
from model.conversion import graph_to_turtle


@command()
async def describe(interaction: Interaction, entity: Role | Member) -> None:
    """Collect the Concise Bounded Description of the given entity, if available."""
    try:
        graph = get_graph(object_uri(interaction.guild))
        cbd = graph.cbd(object_uri(entity))
    except Exception as ex:
        exception(ex)
        cbd = Graph()
    turtle = graph_to_turtle(cbd)
    content = f"```yaml\n{turtle}```"
    if len(content) > 2000:
        turtle_io = BytesIO(turtle.encode())
        file = File(fp=turtle_io, filename="cbd.yaml")
        await interaction.response.send_message(file=file)
    else:
        await interaction.response.send_message(content=content)


async def create_command_tree(client: Client) -> CommandTree:
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
    tree.add_command(describe)

    async def on_error(interaction: Interaction, error: AppCommandError) -> None:
        await interaction.response.send_message(
            content=f"```yaml\n{str(error)}\n```",
            ephemeral=True,
        )

    tree.error(on_error)
    for guild in client.guilds:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)
    return tree
