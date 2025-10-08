import asyncio
import uuid
from datetime import datetime

jobs = {}
job_queue = asyncio.Queue()

# Enqueue a task in the job queue
async def enqueue(callback: callable, req):
    task_id = str(uuid.uuid4())
    jobs[task_id] = {"status": "pending", "output": []}
    await job_queue.put((task_id, callback, req))
    return {"task_id": task_id, "status": "init"}

# Dequeue a task in the job queue
async def dequeue():
    return (await job_queue.get())

# Mark task in queue as done
async def mark_done():
    job_queue.task_done()

# Write message to task data for 'task_id'
def write(task_id: str, message: str) -> str:
    final_message = "{}: {}".format(
        datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        message,
    )
    jobs[task_id]["output"].append(final_message)
    return "updated"

# Write failure to task data
def failure(task_id: str, message: str = None) -> str:
    jobs[task_id]["status"] = "failed"
    if message: write(task_id, message)
    return "failed"
