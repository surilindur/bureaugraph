[![Workflow status](https://github.com/surilindur/skeevaton/workflows/CI/badge.svg)](https://github.com/surilindur/skeevaton/actions?query=workflow%3ACI)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Experimental Discord bot for logging various things in community servers on Discord,
such as message edits and deletions.
The bot will only perform logging for messages that are found in its local message cache,
and will therefore be unsuitable for use on large servers with a lot of traffic,
or for logging events related to older messages.
Caching everything is an option, as well, but requires excessive resources.

The bot is intended to be self-hosted, registered in Discord developer portal by the user, and added to a server.
**There exists no public instance of the bot.** Use at your own risk.

## Configuration

The following environment variables can be used to configure the bot.

| Variable         | Description                                        |
|:-----------------|:---------------------------------------------------|
| `LOG_LEVEL`      | `info`, `debug`, `error`                           |
| `DISCORD_TOKEN`  | The token used to log in with the bot              |
| `HISTORY_LENGTH` | Number of messages per channel to cache on startup |
| `HISTORY_WEEKS`  | Maximum number of weeks to cache on startup        |

## License

This code is released under the [MIT license](http://opensource.org/licenses/MIT).
