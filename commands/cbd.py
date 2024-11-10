from re import compile
from logging import warning

from discord.commands import option
from discord.commands import guild_only
from discord.ext.commands import cooldown
from discord.ext.commands import BucketType
from discord.commands.context import ApplicationContext

from client.bot import bot
from graph.storage import graph
from graph.convert import uri as object_uri
from graph.convert import cbd
from graph.utilities import parse_discord_uri
from commands.utilities import graph_to_yaml

USER_REGEX = compile(r"^https:\/\/discord\.com\/users\/(?P<id>[0-9]+)$")


@bot.slash_command(
    name="cbd",
    description="Collect the Concise Bounded Description (CBD) of the given entity",
)
@option(name="uri", input_type=str, description="The URI of the entity")
@cooldown(rate=1, per=10, type=BucketType.user)
@guild_only()
async def command_cbd(context: ApplicationContext, uri: str) -> None:

    content = None
    file = None

    guild_uri = object_uri(context.guild)
    guild_graph = await graph(guild_uri)

    uri = await parse_discord_uri(uri)
    uri_cbd = guild_graph.cbd(uri)

    guild_graph.close()

    if not uri_cbd:
        user_match = USER_REGEX.fullmatch(uri)
        if user_match:
            warning(f"Retrieving user from Discord API <{uri}>")
            discord_user = await bot.fetch_user(int(user_match.group("id")))
            uri_cbd = cbd(discord_user)

    if uri_cbd:
        content, file = await graph_to_yaml(uri_cbd, "cbd.yaml")
    else:
        content = f"```yaml\nNot found: <{uri}>\n```"

    uri_cbd.close()

    await context.respond(content=content, file=file)
