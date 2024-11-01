from io import BytesIO
from logging import error

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

from client.storage import get_guild_graph

from model.conversion import object_to_uri
from model.conversion import graph_to_turtle


@command()
async def describe(interaction: Interaction, entity: Role | Member) -> None:
    """Collect the Concise Bounded Description of the given entity, if available."""
    try:
        graph = get_guild_graph(interaction.guild)
        uri = object_to_uri(entity)
        cbd = graph.cbd(uri)
    except Exception as ex:
        error(ex)
        cbd = Graph()
    turtle_io = BytesIO(graph_to_turtle(cbd).encode())
    file = File(fp=turtle_io, filename="cbd.txt")
    await interaction.response.send_message(file=file)


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
    tree.add_command(describe)

    async def on_error(interaction: Interaction, error: AppCommandError) -> None:
        await interaction.response.send_message(
            content=f"```yaml\n{str(error)}\n```",
            ephemeral=True,
        )
        await client.on_error(
            "app_command",
            error=str(error),
            user_integration=interaction.is_user_integration(),
            guild_integration=interaction.is_guild_integration(),
            created_at=interaction.created_at.isoformat(timespec="seconds"),
            user_name=interaction.user.name,
            user_id=interaction.user.id,
        )

    tree.error(on_error)
    return tree
