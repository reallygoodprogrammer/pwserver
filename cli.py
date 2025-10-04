import requests
import getopt
import sys
import time
from datetime import datetime

from settings import BASE_URL
from pwserver import config

# List Tasks
# 
# Requests and lists all of the task-ids from the
# server.
def list_all():
    data = requests.get(BASE_URL + "/list").json()
    for t, s in data.items():
        print(f"{t}: {s}")
    sys.exit(0)


# Task Status
#
# Get the status and logs of a task by its task_id
def status(task_ids):
    def printr(v, indent=0):
        if type(v) == type([]):
            print("")
            for vi in v:
                for i in range(indent): print("\t", end="")
                printr(vi, indent+1)
        elif type(v) == type({}):
            print("")
            for k, vi in v.items():
                for i in range(indent): print("\t", end="")
                print(k, ": ", end="")
                printr(vi, indent+1)
        else:
            print(v)

    for t in task_ids:
        response = requests.get(BASE_URL + f"/status?task_id={t}")
        if response.status_code < 400:
            printr(response.json())
    sys.exit(0)

# Display Help
#
# status_code 
#       -> if not `None`, exit after print w/ status
def help(status_code: int = None, module: str = None, modules: dict = {}):
    if not module:
        print("usage: python3 cli.py <module> [OPTIONS] [<args>,]\n")
        for k, m in config.client_modules.items(): print(f"{k}\t{m['description']}")
        print("\n-l/--list\t\tlist the currently running tasks w/ status")
        print("-s/--status <ID>\tretrieve the status / logs for task_id ID")
    elif len(modules.keys()) > 0 and module:
        print("\n".join(config.client_modules[module]["help"]))
    if status_code is not None: sys.exit(status_code)


# ...
def main():
    if len(sys.argv) == 1:
        help(1)
    elif sys.argv[1] in ["-h", "--help"]: 
        help(0)
    elif sys.argv[1] in ["-l", "--list"]:
        list_all()
    elif sys.argv[1] in ["-s", "--status"]:
        status(sys.argv[2:])
    elif sys.argv[1] not in config.client_modules.keys():
        print(f"unknown module: {sys.argv[1]}")
        help(1)

    output = config.client_modules[sys.argv[1]]["entry"](BASE_URL, sys.argv[2:])
    if output:
        print(output)
    else:
        help(1, sys.argv[1], config.client_modules)

if __name__ == "__main__":
    main()
