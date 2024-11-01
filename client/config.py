from os import getenv
from typing import Tuple

from client.constants import AVAILABLE_LOG_LEVELS


def get_log_level() -> int:
    """Get the current log level as an integer."""
    return AVAILABLE_LOG_LEVELS[getenv("LOG_LEVEL", "info")]


def get_discord_token() -> str:
    """Get the Discord token used to authenticate the bot."""
    return getenv("DISCORD_TOKEN")


def get_sparql_auth() -> Tuple[str, str]:
    """Get the SPARQL endpoint username and password tuple."""
    return (getenv("SPARQL_USERNAME"), getenv("SPARQL_PASSWORD"))


def get_sparl_query_endpoint() -> str:
    """Get the SPARQL query endpoint URI."""
    return getenv("SPARQL_ENDPOINT_QUERY")


def get_sparql_update_endpoint() -> str:
    """Get the SPARQL update endpoint URI."""
    return getenv("SPARQL_ENDPOINT_UPDATE")
