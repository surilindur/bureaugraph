from typing import Dict
from platform import python_version
from platform import system
from platform import machine
from platform import python_implementation

from rdflib.term import URIRef
from rdflib.graph import Graph
from rdflib.graph import Dataset
from rdflib.store import Store
from rdflib.plugins.stores.sparqlstore import SPARQLUpdateStore

from discord import version_info

from client.bot import bot
from client.config import SPARQL_ENDPOINT_QUERY
from client.config import SPARQL_ENDPOINT_UPDATE
from client.config import SPARQL_AUTH

_cache: Dict[str, Store | Dataset] = {}


async def user_agent() -> str:
    """Generates an HTTP User-Agent string for use in network requests."""
    app_name = (await bot.application_info()).name
    ua_header = " ".join(
        (
            f"{app_name}/1.0 ({system()} {machine()})",
            f"Pycord/{version_info.major}.{version_info.minor}.{version_info.micro}",
            f"{python_implementation()}/{python_version()}",
        )
    )
    return ua_header


async def store() -> Store:
    """Creates the SPARQL store instance to back all the graphs."""
    if "store" not in _cache:
        _cache["store"] = SPARQLUpdateStore(
            query_endpoint=SPARQL_ENDPOINT_QUERY,
            update_endpoint=SPARQL_ENDPOINT_UPDATE,
            sparql11=True,
            context_aware=True,
            autocommit=False,
            method="POST_FORM",
            returnFormat="json",
            headers={"User-Agent": await user_agent()},
            auth=SPARQL_AUTH,
        )
    return _cache["store"]


async def dataset() -> Dataset:
    """Creates the RDF dataset instance where all the graphs are managed."""
    if "dataset" not in _cache:
        _cache["dataset"] = Dataset(
            store=await store(),
            default_union=True,
        )
    return _cache["dataset"]


async def graph(uri: URIRef) -> Graph:
    """Creates the RDF graph for the specificed URI, or returns an existing one."""
    default_dataset = await dataset()
    uri_graph = default_dataset.graph(identifier=uri)
    return uri_graph
