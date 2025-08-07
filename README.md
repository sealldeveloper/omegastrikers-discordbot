# Omega Strikers - Gamblers Cup Drafts Bot

A small Discord bot for the 2nd Gamblers Cup to do randomised draft rolls for strikers.

## Installation

The installation is done with `uv`.

Setup the `.env` file by renaming `.env.sample` to `.env`. Set the Discord bot token and the Guild ID that the bot will run in.

Then invite the bot to the server, and run it with the following:
```
$ uv run main.py
```

## Usage
- `/startdraft` - Starts a draft for that channel/thread
- `/roll` - Rolls a random striker
- `/enddraft` - Completes the draft in that channel


