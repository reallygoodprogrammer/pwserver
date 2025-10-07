from typing import TypeVar, Type, Generic
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from . import tasks

_JsonType = TypeVar("JsonType", bound=BaseModel)

# Base Plugin
#
# Base class for creating a plugin to be managed by
# pwserver.
class BasePlugin(Generic[_JsonType]):
    _router: APIRouter
    _name: str

    def __init__(
        self, 
        name: str, 
        datatype: Type[_JsonType],
        description: str = None,
    ):
        assert name and name[0] != "/", "plugin 'name' cannot start with '/'"
        self.name = name
        self._datatype = datatype
        self.description = description
        self._router = APIRouter(
            prefix="/" + name,
        )

        # self._client_help -> client help message
        self._client_help_msg = [
            f"usage: client.py {name} [options] <route>\n",
            "{:28}method: specify the method to use for the route".format("-X/--method"),
        ]
        # self._short_opts -> getopt short options string
        self._args = ["route"]
        self._short_opts = "hX:"
        # self._long_opts -> getopt long options list
        self._long_opts = ["help", "method="]
        # self._field_types -> mapping of field names to field types for conversion
        self._field_types = {
            "help": bool,
            "method": str,
        }
        # self._option_mappings -> dict of getopt option flag to field name
        self._option_mappings = {
            "-h": "help",
            "--help": "!_help",
            "-X": "!_method",
            "--method": "!_method",
        }

        # mapping of route paths to method type
        self.routes = []
        self._route_method = {}

        for field, info in self._datatype.model_fields.items():
            self._field_types[field] = info.annotation
            if info.is_required():
                self._args.append(field)
                self._client_help_msg[0] += f" <{field}>"
            else:
                so = None
                if field[0].lower() not in self._short_opts:
                    so = field[0].lower()
                elif field[0].upper() not in self._short_opts:
                    so = field[0].upper()
                lo = field

                if so: self._option_mappings["-" + so] = field
                self._option_mappings["--" + lo] = field

                self._client_help_msg.append(
                    "{:28}{}: '{}' value{}".format(
                        "{}{}".format(
                            "-" + so + "/" if so else "",
                            "--" + lo,
                        ),
                        field,
                        str(info.annotation).split("'")[1],
                        f" [default={info.default}]" if info.default else "",
                    )
                )

                if info.annotation != bool:
                    if so: so += ":"
                    lo += "="
                if so: self._short_opts += so
                self._long_opts.append(lo)


    def __str__(self):
        return f"{self.name}"


    def get(self, route: str):
        def wrapper(func):
            self._router.get(route)(self._setup_route_callback(func))
            self.routes.append(route)
            if route not in self._route_method.keys():
                self._route_method[route] = []
            elif "GET" in self._route_method[route]:
                raise Exception(f"route {route} with method 'GET' already exists")
            self._route_method[route].append("POST")
            return func
        return wrapper

    def post(self, route: str):
        def wrapper(func):
            self._router.post(route)(self._setup_route_callback(func, "POST"))
            self.routes.append(route)
            if route not in self._route_method.keys():
                self._route_method[route] = []
            elif "POST" in self._route_method[route]:
                raise Exception(f"route {route} with method 'POST' already exists")
            self._route_method[route].append("POST")
            return func
        return wrapper

    # returns the routing function based on appropriate task callback
    def _setup_route_callback(self, callback: callable, method: str = "GET"):
        model = self._datatype
        if method == "POST":
            async def route_callback(body: model): 
                return (await tasks.enqueue(callback, body))
            return route_callback
        elif method == "GET":
            async def route_callback(body: model = Depends()):
                return (await tasks.enqueue(callback, body))
            return route_callback
        raise Exception(f"method {method} setup callback is undefined")


    # Client function
    def client_entry(self, base_url: str, *args):
        import getopt
        import requests

        opts, args = getopt.getopt(*args, self._short_opts, self._long_opts)

        if len(self._args) != len(args):
            return self._client_help(f"no '{self._args[len(args)]}' argument provided")

        route = args[0]
        method = "GET"
        if "/" + route in self.routes:
            route = "/" + route
        elif route not in self.routes:
            return self._client_help(f"invalid route: {route}")
        
        fargs = {}
        for i, a in enumerate(args[1:]):
            field = self._args[i]
            fargs[field] = self._field_type[field](a)

        fopts = {}
        for o, a in opts:
            if o in self._option_mappings.keys():
                field = self._option_mappings[o]
                if field == "!_help":
                    self._client_help()
                elif field == "!_method":
                    if a not in self._route_method[route]:
                        raise Exception(f"unsupported 'method' option: {a}")
                    method = a
                else:
                    fopts[field] = self._field_types[field](a)

        body = self._datatype(**fargs, **fopts).model_dump()

        resp = None
        if method == "GET":
            resp = requests.get(f"{base_url}/{self.name}{route}", params=body)
        elif method == "POST":
            resp = requests.post(f"{base_url}/{self.name}{route}", json=body)
        return resp.json()
            

    # returns help message
    def _client_help(self, msg: str = None) -> str:
        if msg: return "\n".join(["\033[31m" + msg + "\033[0m"] + self._client_help_msg)
        return "\n".join(self._client_help_msg)
