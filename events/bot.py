from logging import info
from logging import error
from logging import exception
from traceback import format_exc
from traceback import format_exception

from discord.enums import Status
from discord.activity import CustomActivity
from discord.errors import DiscordException
from discord.errors import ApplicationCommandError
from discord.commands.context import ApplicationContext

from client.bot import bot
from graph.convert import uri
from updates.guild import synchronise_guilds


@bot.event
async def on_ready() -> None:
    info(f"Logged in as <{uri(bot.user)}>")
    await synchronise_guilds(bot.guilds)
    await bot.change_presence(
        activity=CustomActivity(
            name="Observing",
            extra="Registering events as they happen",
        ),
        status=Status.online,
    )
    info("Initialisation flow complete")


@bot.event
async def on_error(event: str, *args, **kwargs) -> None:
    error(f"Event handling failed: {event}")
    exception(format_exc())
    await bot.change_presence(
        activity=CustomActivity(
            name="Experiencing issues",
            extra="Still registering events",
        ),
        status=Status.idle,
    )


@bot.event
async def on_application_command_error(
    context: ApplicationContext,
    ex: DiscordException,
) -> None:
    error(f"Application command failed: {"".join(format_exception(ex))}")
    if isinstance(ex, ApplicationCommandError):
        ex = ":".join(str(ex).split(":")[2:]) or str(ex)
    await context.respond(content=f"```yaml\n{ex}\n```")
