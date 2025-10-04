import time
import asyncio
import os
from playwright.async_api import async_playwright


from . import config
from . import tasks

pw = None
browser = None
headless = bool(int(os.getenv("PW_HEADLESS", False)))

actions = {}
print(config.actions.values())
for module in config.actions.values():
    for k, v in module.items():
        actions[k] = v

async def taskloop():
    while True:
        task_id, action, *args = await tasks.job_queue.get()
        tasks.jobs[task_id]["status"] = "pending"
        asyncio.create_task(process(task_id, action, *args))
        tasks.job_queue.task_done()

async def start_browser():
    global pw
    global browser
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)

async def stop_browser():
    await pw.stop()

# process some action, using the actions dict
async def process(task_id: str, action: str, *args):
    if action not in actions.keys():
        raise Exception(f"no action called '{action}' exists")
    ctx = await browser.new_context()
    tasks.jobs[task_id]["output"] = []
    try:
        tasks.jobs[task_id]["status"] = await actions[action](tasks.jobs[task_id], ctx, *args)
    except Exception as e:
        tasks.jobs[task_id]["status"] = "failed"
        tasks.jobs[task_id]["output"].append(f"error: {e}")
        raise(e)
    await ctx.close()
