from os import getenv
from typing import Dict
from logging import basicConfig, DEBUG, INFO, ERROR

LOG_LEVELS: Dict[str, int] = {
    "info": INFO,
    "debug": DEBUG,
    "error": ERROR,
}

HISTORY_LENGTH = int(getenv("HISTORY_LENGTH", "100"))
HISTORY_WEEKS = int(getenv("HISTORY_WEEKS", "104"))

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"

DISCORD_TOKEN = getenv("DISCORD_TOKEN")
LOGGING_LEVEL = getenv("LOG_LEVEL", "info")

basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=LOG_LEVELS[LOGGING_LEVEL],
)
