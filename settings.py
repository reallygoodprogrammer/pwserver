from mods import cl

BASE_URL = "http://127.0.0.1:8000"

CLIENT_MODULES = {
    "cl": cl.CLIENT_SETTINGS,
}

ACTIONS = {
    "cl": cl.ACTIONS,
}

ROUTERS = [
    cl.ROUTER,
]
