# pwserver

*A server for running and logging playwright code*


A **plugin** is defined as some custom python playwright code that is
ran and managed by the server.

The purpose of this application is to provide a way to run custom plugins
that can be accessed and ran through the servers API to manage playwright
scripts and scheduling.

Notice that this server isn't intended to be publicly accessible and would
likely need further configuration to meet such task.

## Basic Setup

You will need to create two folders in the root directory of the
repo: `data` and `mods`. You can also configure this to some other
paths in the `docker-compose.yml` volume mounts, that is just the current
default mount locations used.

```bash
# Clone and cd into repo. Then:
mkdir data
mkdir mods
```

Any plugins will need to be added in the `mods` directory.

Any data accessed by said plugins will need to be put in the `data` 
directory and can be accessed by plugin code using the `/data` path 
at runtime (assuming server is being ran by docker).

## Usage

To start the server, use `docker compose up`.

At this point, you can create something that accesses the server's API (ex. UI),
or use the CLI app `cli.py` if your plugins have client functions:

```bash
usage: python3 cli.py <module> [OPTIONS] [<args>,]

-l/--list		list the currently running tasks w/ status
-s/--status <ID>	retrieve the status / logs for task_id ID
```

---

## Writing / Configuring Plugins

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

