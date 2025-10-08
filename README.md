# pwserver

***A server for running, scheduling, and simplifying multiple playwright jobs***

---

A **plugin** is defined as some custom python playwright job that is
ran and managed by the server but written by you, the developer.

The purpose of `pwserver` is to provide an API interface for managing multiple
playwright jobs, job scheduling tasks, task logging, and whatnot all within a
single playwright process. The `pwserver` library provides a framework for creating
simple plugins that automate the process of creating the API endpoints and a client
for interact with said endpoints. Instructions for creating a plugin is described
below.

## Usage

The server can be started using uvicorn:

```bash
uvicorn pwserver.server:app
```

The client can be ran using the `client.py` script:

```bash
usage: python3 client.py <module> [options] [<args>,]


# loaded module names and descriptions will appear here

-l/--list               list the currently running tasks w/ status
-s/--status <ID>        retrieve the status / logs for task_id ID
```

---

## Plugins

Writing plugins for use with `pwserver` should be easy and painless. Here are some
instructions on creating your first plugin.

### Define Your Plugin

You will need to create a class extending pydantic's `BaseModel` which will
define all of the input arguments and options that your plugin needs to run.
After that you can create a `BasePlugin` instance using the pydantic class:

```python3
import pwserver.plugins as plugins
from pydantic import BaseModel

def JobData(BaseModel):
    # without a default, the argument is required
    url: str
    # with a default, the argument is not required
    optional_arg: bool = False

my_plugin = pwserver.BasePlugin(
    name='my-plugin',
    datatype=JobData,
    description='my first pwserver plugin',
)
```

### Create Your Plugin's Routes

From there you can create functions that will take a job's `task_id`, instance of a pw browser
context, and instance of your extended pydantic model as arguments. Then use the appropriate
decorator for adding the job to your plugin instance:

```python3
# for writing output from the job:
from pwserver.tasks import write


# use @my_plugin.post(route) for post method w/ json data
@my_plugin.get("/get_url_title")
async def update_all(task_id: int, ctx, body: JobData):
    page = ctx.new_page()
    page.goto(body.url)
    title = page.locator('title').inner_text()
    write(task_id, f"the title of the page is " + title) 
    page.close()
```

### Add Your Plugin to `pwserver`

The last thing you will need to do is add your plugin in the `settings.py` file within
the `PLUGINS` dictionary like so:

```python3
from my_plugin_file import my_plugin

# ...

plugins = {
    "my-plugin": my_plugin,
}
```

Congrats! Once you've completed all of that you have created your first `pwserver` plugin!

A client interface will be automatically generated for your plugin accessible with the 
`client.py` script.

---

## License

This project licensing falls under the MIT License which found in the [LICENSE](LICENSE)
file in this repo.
