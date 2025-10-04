from mods import cl

# The url that the server should host on
#
# This should typically remain its default in most cases
BASE_URL = "http://127.0.0.1:8000"

# Map of module names to module import
# 
# Add all of your plugins for pwserver here!
PLUGINS = {
    "cl": cl_plugin,
}
