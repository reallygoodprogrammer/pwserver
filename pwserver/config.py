import settings

routers = []
plugins = settings.PLUGINS

for p, v in settings.PLUGINS.items():
    try:
        routers.append(v._router)
    except Exception as e:
        raise Exception(f"failed loading router from plugin class '{p}': {e}")
