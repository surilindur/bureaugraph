from typing import Dict

from discord.guild import Guild

from rdflib.graph import Graph
from rdflib.graph import Dataset
from rdflib.store import Store
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from model.conversion import object_to_uri

from client.constants import USER_AGENT
from client.config import get_sparl_query_endpoint
from client.config import get_sparql_update_endpoint
from client.config import get_sparql_auth

_cached_data: Dict[str, Store | Dataset] = {}


def get_store() -> Store:
    """Get the default store."""
    if "store" not in _cached_data:
        _cached_data["store"] = SPARQLUpdateStore(
            query_endpoint=get_sparl_query_endpoint(),
            update_endpoint=get_sparql_update_endpoint(),
            sparql11=True,
            context_aware=True,
            autocommit=False,
            method="POST_FORM",
            returnFormat="json",
            headers={"User-Agent": USER_AGENT},
            agent=USER_AGENT,
            auth=get_sparql_auth(),
        )
    return _cached_data["store"]


def get_dataset() -> Dataset:
    """Get the dataset of the default store."""
    if "dataset" not in _cached_data:
        _cached_data["dataset"] = Dataset(
            store=get_store(),
            default_union=True,
        )
    return _cached_data["dataset"]


def get_guild_graph(guild: Guild) -> Graph:
    guild_uri = object_to_uri(guild)
    guild_graph = get_dataset().graph(identifier=guild_uri)
    return guild_graph
