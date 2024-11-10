from os import getenv
from typing import Dict
from logging import INFO
from logging import DEBUG
from logging import ERROR
from logging import WARNING
from logging import addLevelName
from logging import basicConfig

# The allowed levels for logging, to map from user input to integer values
_AVAILABLE_LOG_LEVELS: Dict[str, int] = {
    "debug": DEBUG,
    "info": INFO,
    "warning": WARNING,
    "error": ERROR,
}

# Override the names so they match the user-visible ones
for name, level in _AVAILABLE_LOG_LEVELS.items():
    addLevelName(level, name)

# Configure logging immediately upon importing this file
basicConfig(
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    level=_AVAILABLE_LOG_LEVELS[getenv("LOG_LEVEL", "info")],
)

# Discord token
DISCORD_TOKEN = getenv("DISCORD_TOKEN")
assert DISCORD_TOKEN, "Discord token not provided"

# SPARQL endpoints for querying and updating
SPARQL_ENDPOINT_QUERY = getenv("SPARQL_ENDPOINT")
assert SPARQL_ENDPOINT_QUERY, "SPARQL query endpoint not provided"
SPARQL_ENDPOINT_UPDATE = getenv("SPARQL_ENDPOINT_UPDATE", SPARQL_ENDPOINT_QUERY)
assert SPARQL_ENDPOINT_UPDATE, "SPARQL update endpoint not provided"

# SPARQL endpoint authentication
_SPARQL_USERNAME = getenv("SPARQL_USERNAME")
_SPARQL_PASSWORD = getenv("SPARQL_PASSWORD")
SPARQL_AUTH = (
    (_SPARQL_USERNAME, _SPARQL_PASSWORD)
    if _SPARQL_USERNAME and _SPARQL_PASSWORD
    else None
)
