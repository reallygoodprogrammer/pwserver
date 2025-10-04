# pwserver

*A server for running and logging playwright code*

The purpose of this application is to provide a way to run custom 
playwright 'plugins' that can be accessed and ran through the servers
API endpoints.

A **plugin** is defined as some custom python playwright code that is
ran and managed by the server.

## Basic Setup

You will need to create two folders in the root directory of the
project: `data` and `mods`. You can also configure this to some other
folders in the `docker-compose.yml` volume mounts, that is just the current
default mount locations used.

```bash
# Clone and cd into repo. Then:
mkdir data
mkdir mods
```

Any plugin will need to be put in `mods`.

Any data accessed by said plugin will need to be put in `data` and can be
accessed through the `/data` path at runtime.

## Usage

To start the server, use `docker compose up`.

At this point, you can have something that accesses the server's API (ex. UI),
or use the CLI app `cli.py` if your plugins have client functions:

```bash
usage: python3 cli.py <module> [OPTIONS] [<args>,]

-l/--list		list the currently running tasks w/ status
-s/--status <ID>	retrieve the status / logs for task_id ID
```

---

## Writing Plugins

There are a few globals and fastapi specific configurations that will
need to be defined in your plugin:

`CLIENT_SETTINGS` will define the configuration for your cli.py function.

```python3
# Client Settings
#
#   entry:          method that is ran by `python3 cli.py <plugin name>`
#   description:    short description of modules purpose
#   help:           array of lines to display on -h/--help options
CLIENT_SETTINGS = {
    "entry": scraper_client_function,
    "description": "scraper plugin for pwserver",
    "help": [
        "usage: cl [OPTIONS] [ARGS]\n",
        "-h/--help      display this help message",
        # other options explained here
    ],
}
```

**I will be adding more documentation on this once the system for writing
plugins is better functioning**

