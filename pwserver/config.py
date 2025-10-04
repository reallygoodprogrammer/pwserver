import settings

routers = []

for p, v in settings.PLUGINS.items():
    try:
        routers.append(v._router)
    except Exception as e:
        raise Exception(f"failed loading router from plugin class '{v}': {e}")
