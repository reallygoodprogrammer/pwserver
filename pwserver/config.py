import settings

routers = []
client_modules = {}
actions = {}

for m, v in settings.MODULES.items():
    try:
        routers.append(v.ROUTER)
        client_modules[m] = v.CLIENT_SETTINGS
        actions[m] = v.ACTIONS
    except Exception as e:
        raise Exception(f"FAILED LOADING CLIENT MODULES: {e}")
