# Bureaugraph

<p align="left">
  <a href="https://github.com/surilindur/bureaugraph/actions/workflows/ci.yml"><img alt="Workflow: CI" src=https://github.com/surilindur/bureaugraph/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

Bureaugraph is an experimental Discord bot for learning purposes, and is not designed to handle large servers.
The purpose of the bot is to provide interesting insights for administrators of smaller servers.

> [!CAUTION]
> The bot is currently work-in-progress and should not actually be used, except for testing purposes.

## Dependencies

The Python dependencies are listed in [requirements.txt](./requirements.txt).
Additionally, a SPARQL endpoint is needed to store the data of the bot.

## Configuration

The bot can be configured using a set of environment variables:

* `DISCORD_TOKEN`: The token to authenticate to Discord API.
* `SPARQL_ENDPOINT_QUERY`: The SPARQL query endpoint URI.
* `SPARQL_ENDPOINT_UPDATE`: The SPARQL update endpoint URI.
* `SPARQL_USERNAME`, `SPARQL_PASSWORD`: The credentials used to authenticate to the SPARQL endpoint.
* `LOG_LEVEL` The logging level to use, choices are `info`, `debug`, `warning` and `error`

## Issues

While the bot is not expected to function properly,
any issues can still be reported on the GitHub issue tracker.

## License

This code is copyrighted and released under the [MIT license](http://opensource.org/licenses/MIT).
