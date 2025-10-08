import time
import asyncio
import os
from playwright.async_api import async_playwright

from . import config
from . import tasks

pw = None
browser = None
headless = bool(int(os.getenv("PW_HEADLESS", False)))

async def taskloop():
    while True:
        task_id, action, req = await tasks.dequeue()
        asyncio.create_task(process(task_id, action, req))
        await tasks.mark_done()

async def start_browser():
    global pw
    global browser
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)

async def stop_browser():
    await pw.stop()

async def process(task_id: str, action: callable, req):
    ctx = await browser.new_context()
    try:
        await action(task_id, ctx, req)
    except Exception as e:
        tasks.failure(task_id, f"exception occured during runtime: {e}")
    await ctx.close()
