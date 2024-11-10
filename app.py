from os import scandir
from logging import debug
from importlib import import_module

from client.bot import bot
from client.config import DISCORD_TOKEN

MODULE_EXTENSION = ".py"


def load_modules(package: str) -> None:
    for fp in scandir(package):
        if fp.name.endswith(MODULE_EXTENSION):
            name = fp.name.removesuffix(MODULE_EXTENSION)
            load_target = f"{package}.{name}"
            debug(f"Loading module {load_target}")
            import_module(load_target)


def main() -> None:
    for package in ("events", "commands"):
        load_modules(package)
    bot.run(token=DISCORD_TOKEN)


if __name__ == "__main__":
    main()
