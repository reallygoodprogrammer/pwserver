from typing import TypeVar, Type, Generic
from fastapi import APIRouter

JsonType = TypeVar("JsonType")

# Base Plugin
#
# Base class for creating a plugin to be managed by
# pwserver.
class BasePlugin(Generic[JsonType]):
    _router: APIRouter
    _name: str

    def __init__(
        self, 
        name: str, 
        datatype: Type[JsonType],
        description: str = None,
    ):
        self._name = name
        self._datatype = datatype
        self._description = description
        self._router = APIRouter(
            prefix=name,
        )

        self._opts = [
            ("help", "h", bool, "display help message", False),
        ]

        for field, info in self._datatype.model_fields.items():
            shorts = [x[1] for x in self._opts]
            short_opt = None
            if field[0] not in shorts:
                short_opt = field[0]
            elif (
                field[0] in shorts and 
                field[0].uppercase() not in shorts
                ):
                short_opt = field[0].uppercase()

            help_msg = f"type: {_type[info.annotation]}"
            required = False
            if info.default == PydanticUndefined:
                required = True
                help_msg += " *required*"

            self._opts.append(
                (field, short_opt, info.annotation, help_msg, required)
            )

    def __str__(self):
        return f"{self.name}"


    def get(self, route: str):
        def wrapper(func):
            self._router.get(r.route)(self._setup_route_callback(func))
            return func
        return wrapper

    def post(self, route: str):
        def wrapper(func):
            self._router.post(r.route)(self._setup_route_callback(func))
            return func
        return wrapper

    def _setup_route_callback(self, callback: callable):
        def route_callback(body: JsonType): 
            return (await tasks.enqueue(callback, body))
        return route_callback

    def _client_entry(self, *args):
        import getopt

        opts, args = getopt.getopt(*args, self._short_opts, self._long_opts)
        for o, a in opts:
            for i in range(self._long_opts):
                if 



