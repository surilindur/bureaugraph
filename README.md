<p align="center">
  <img alt="icon" src="./images/icon.png" width="80">
</p>

<p align="center">
  <a href="https://github.com/surilindur/apparatus/actions/workflows/ci.yml"><img alt="Workflow: CI" src=https://github.com/surilindur/apparatus/actions/workflows/ci.yml/badge.svg?branch=main"></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-yellow.svg"></a>
</p>

**Apparatus** is an experimental Discord bot for learning purposes.
There exists no public instance of the bot due to its experimental nature,
and interested users are expected to run one themselves.
The bot is not optimised to handle large servers, rather,
it is designed to offer interesting niche features on smaller servers with less traffic.
Most of the features require the bot to cache a considerable portion of -- if not the entire --
message history on any server it is added,
to be able to properly carry out its tasks.

The following environment variables can be used to configure the bot:

* `LOG_LEVEL` The logging level to use, choices are `info`, `debug` and `error`
* `DISCORD_TOKEN` The token used to log in with the bot
* `HISTORY_MINIMUM` The minimum message cache size
* `HISTORY_LENGTH` Number of messages per channel to cache on startup
* `HISTORY_WEEKS` Maximum number of weeks to cache on startup
