from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
import asyncio
import uuid

from . import taskloop
from . import tasks

from settings import ROUTERS

# FastAPI
app = FastAPI(
    title="pwserver",
    version="0.1.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await taskloop.start_browser()
    asyncio.create_task(taskloop.taskloop())

@app.on_event("shutdown")
async def shutdown_event():
    await taskloop.stop_browser()

@app.get("/list")
async def list(status: str = None):
    jobs = {}
    keys = (
        tasks.jobs.keys()
        if not status
        else [k for k, v in tasks.jobs.keys() if v["status"] == status]
    )
        
    for job in keys:
        jobs[job] = tasks.jobs[job]["status"]
    return jobs

@app.get("/status")
async def status(task_id: str):
    if task_id not in tasks.jobs.keys():
        return {"output": f"invalid task id '{task_id}'"}
    return tasks.jobs[task_id]


for r in ROUTERS:
    app.include_router(r)
