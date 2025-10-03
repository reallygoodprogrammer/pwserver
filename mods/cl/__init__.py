from fastapi import APIRouter
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
from pydantic import BaseModel
import asyncio
import json
import time
import random
import requests
import uuid

import pwserver.tasks as tasks

# Client Function

def cl_cli(BASE_URL, *args):
    import getopt

    _name = "cl"
    _all = False
    _file = "data/cl/categories.json"
    _city = "portland"
    _tmin = None
    _tmax = None

    opts, args = getopt.getopt(*args, "as:c:p:h", [
        "all", 
        "categories-file=", 
        "city=",
        "persistent=",
        "help"
    ])
    for o, a in opts:
        if o in ["-a", "--all"]:
            _all = True
        elif o in ["-C", "--categories-file"]:
            _file = a
        elif o in ["-c", "--city"]:
            _city = a
        elif o in ["-p", "--persistent"]:
            values = a.split("-")
            if len(values) > 2:
                print(f"invalid time(s) format: {a}")
                return None
            elif len(values) == 2:
                _tmin, _tmax = values
            elif len(values) == 1:
                _tmin = values[0]
                _tmax = values[0]
        elif o in ["-h", "--help"]:
            return None

    if _all:
        if _tmin:
            response = requests.post(f"{BASE_URL}/{_name}/update_all", json={
                "categories_file": _file,
                "city": _city,
                "persistent": True,
                "tmin": _tmin,
                "tmax": _tmax,
            })
            return response
        response = requests.post(f"{BASE_URL}/{_name}/update_all", json={
            "categories_file": _file,
            "city": _city,
        })
        return response

    if len(args) == 0:
        return None

    if _tmin:
        response = requests.post(f"{BASE_URL}/{_name}/update", json={
            "categories_file": _file,
            "category": args[0],
            "city": _city,
            "persistent": True,
            "tmin": _tmin,
            "tmax": _tmax,
        })
        return response.json()

    response = requests.post(f"{BASE_URL}/{_name}/update", json={
        "categories_file": _file,
        "category": args[0],
        "city": _city,
    })
    return response.json()

# Client Settings

CLIENT_SETTINGS = {
    "entry": cl_cli,
    "description": "craigslist scraping",
    "help": [
        "usage: cl [OPTIONS] [ARGS]\n",
        "-a/--all\t\t\tupdate data for all craigslist categories",
        "-C/--categories-file\t\tspecify the categories.json file to use",
        "-c/--city\t\t\tspecify the city to update for",
        "-p/--persistent\t\t\tspecify the recurring interval (or range) to repeat (in minutes)",
    ],
}


# Task Settings:

ROUTER = APIRouter(
    prefix="/cl",
    tags=["cl"],
)

class CraigslistData(BaseModel):
    categories_file: str
    category: str
    city: str = "portland"
    all_cities: bool = False
    persistent: bool = False
    tmin: float = (60.0 * 10)
    tmax: float = (60.0 * 10)

@ROUTER.post("/update_all")
async def cl__update_all(req: CraigslistData):
    task_id = str(uuid.uuid4())
    tasks.jobs[task_id] = {"status": "pending"}
    if req.persistent:
        await tasks.job_queue.put((task_id, "cl__update_all_p", req.categories_file, req.city, req.tmin, req.tmax))
    else:
        await tasks.job_queue.put((task_id, "cl__update_all", req.categories_file, req.city))
    return {"task_id": task_id, "status": "init"}

@ROUTER.post("/update")
async def cl__update(req: CraigslistData):
    task_id = str(uuid.uuid4())
    tasks.jobs[task_id] = {"status": "pending"}
    if req.all_cities:
        req.city = None
    if req.persistent:
        await tasks.job_queue.put((task_id, "cl__update_p", req.categories_file, req.category, req.city, req.tmin, req.tmax))
    else:
        await tasks.job_queue.put((task_id, "cl__update", req.categories_file, req.category, req.city))
    return {"task_id": task_id, "status": "init"}

# Task Code:

_RL = 1.0
_BRL = 360.0

# process all category updates using categories_file
# for retrieving categories and associated urls
#
#   p               -> playwright browser page obj
#   categories_file -> file location for categories json file
async def update_all(data, page, categories_file, city=None):
    try:
        with open(categories_file, "r") as f:
            categories = json.load(f)
    except FileNotFoundError:
        data["output"].append(f"the categories file '{categories_file}' does not exist")
        return "failed"

    if len(categories.keys()) == 0:
        data["output"].append(f"the categories file '{categories_file}' does not contain any data")
        return "failed"

    if city:
        if city not in categories.keys():
            data["output"].append(f"the city url data for '{city}' does not exist")
            return "done"
        for c in categories[city].keys():
            await by_category(data, page, c, categories[city][c], city)

    for city, city_data in categories.keys():
        for c in city_data.keys():
            await by_category(data, page, c, city_data[c], city)

    return "done"

async def update_all_p(data, page, categories_file, city=None, tmin=60.0, tmax=60.0):
    while True:
        await update_all(data, page, categories_file, city)
        wait_time = 0.0
        if tmin == tmax:
            wait_time = tmin
        else:
            wait_time = (random.random() * (tmax - tmin)) + tmin
        starts_at = (datetime.now() + timedelta(minutes=wait_time)).strftime("%Y-%m-%d %H:%M:%S")
        data["output"].append(f"{city}: sleeping till {starts_at}")
        await asyncio.sleep(wait_time * 60)

# process a specific category's updates using matching
# categories_file url
#
#   p               -> playwright browser page obj
#   categories_file -> file location for categories json file
#   category        -> the category to update data for
async def update(data, page, categories_file, category, city="portland"):
    try:
        with open(categories_file, "r") as f:
            categories = json.load(f)
    except FileNotFoundError:
        data["output"].append(f"the categories file '{categories_file}' does not exist")
        return "failed"

    if len(categories.keys()) == 0:
        data["output"].append(f"the categories file '{categories_file}' does not contain any files")
        return "failed"

    if not city:
        for c in categories.keys():
            await by_category(data, page, category, categoires[c][category], c)
    elif city not in categories.keys():
        data["output"].append(f"the city url data for '{city}' does not exist")
    else:
        await by_category(data, page, category, categories[city][category], city)

    return "done"

async def update_p(data, page, categories_file, category, city="portland", tmin=60.0, tmax=60.0):
    while True:
        await update(data, page, categories_file, category, city)
        wait_time = 0.0
        if tmin == tmax:
            wait_time = tmin
        else:
            wait_time = (random.random() * (tmax - tmin)) + tmin
        starts_at = (datetime.now() + timedelta(minutes=wait_time)).strftime("%Y-%m-%d %H:%M:%S")
        data["output"].append(f"{city}-{category}: sleeping till {starts_at}")
        await asyncio.sleep(wait_time * 60)



# process the update of a single cl categories
# listing data.
#
#   p -> playwright browser page obj
#   category -> name of the category
#   url -> url of the craigslist category page
#
# returns a message display start and stop times
async def by_category(process, p, category : str, url : str, city : str = "portland"):
    process["output"].append(f"{city}-{category}: started at " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    json_file = f"data/cl/{city}/{category}.json"
    data = get_json_file(json_file)

    urls = list(await get_active_listings(p, url))

    new_active = {}
    for post_id in data["active"].keys():
        post = data["active"][post_id]
        if post["url"] not in urls:
            post["sold"] = True
            data["sold"][post_id] = post
        else:
            post["last-seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            urls.remove(post["url"])
            new_active[post_id] = post
    data["active"] = new_active

    process["output"].append(f"{city}-{category}: retrieving {len(urls)} new posts")
    for i, url in enumerate(urls):
        try:
            new_data = await get_page_data(p, url)
            new_data["last-seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            data["active"][new_data["id"]] = new_data
        except Exception as e:
            process["output"].append(f"{city}-{category}: error at {url}: {e}")

    write_to_json(json_file, data)

    process["output"].append(f"{city}-{category}: ended " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


# Visit and parse data from a craigslist post
#
#   page    -> playwright page object
#   url     -> url of the post to scrape
async def get_page_data(page, url):
    global _RL
    global _BRL

    await asyncio.sleep(_RL)
    data = {}

    await page.goto(url, wait_until="networkidle")

    is_blocked = await page.locator("title").inner_text()
    if "blocked" == is_blocked:
        await asyncio.sleep(_BRL)
        _RL *= 2.5
        new_data = await get_page_data(page, url)
        return new_data
    elif _RL > 1.0:
        _RL *= 0.99
        if _RL < 1.0:
            _RL = 1.0

    data["url"] = url
    data["id"] = (
        (await page.locator(".postinginfo:has-text('post id:')").inner_text()).split(" ")[-1]
    )
    data["title"] = await page.locator(".postingtitletext #titletextonly").inner_text()
    if await page.locator(".price").is_visible():
        data["price"] = float(
            (await page.locator(".price").inner_text()).strip("$").replace(",", "")
        )
    else:
        data["price"] = None
    if await page.locator(".postingtitletext > span").nth(2).is_visible():
        data["title-location"] = (
            (await page.locator(".postingtitletext > span").nth(2).inner_text()).strip(" ()")
        )
    else:
        data["title-location"] = None
    data["description"] = await page.locator("#postingbody").inner_text()
    data["location"] = {
        "area": await page.locator(".crumb.area > p > a").inner_text(),
        "subarea": await page.locator(".crumb.subarea > p > a").inner_text(),
    }
    data["posted"] = await page.locator("#display-date.postinginfo > time").get_attribute("title")

    attributes = {}
    attribute_results = page.locator(".attrgroup > .attr")

    for i in range(await attribute_results.count()):
        if await attribute_results.nth(i).locator(".labl").is_visible():
            key = (await attribute_results.nth(i).locator(".labl").inner_text()).strip(":")
            value = await attribute_results.nth(i).locator(".valu").inner_text()
            attributes[key] = value
        else:
            value = await attribute_results.nth(i).locator(".valu").inner_text()
            if "other" not in attributes.keys():
                attributes["other"] = [value]
            else:
                attributes["other"].append(value)
    data["attributes"] = attributes

    return data


# Return the urls of the active posts found for a craigslist category
# url
#
#   page    -> playwright page object
#   url     -> url of the category page
async def get_active_listings(page, url):
    attributes = {}

    await page.goto(url + "#search=2~list~0", wait_until="networkidle")
    await asyncio.sleep(5)
    total_count = int(
        (await page.locator(".visible-counts > span").nth(1).inner_text()).split(" ")[-1].replace(",", "")
    )
    new_height = 3000

    while len(attributes.keys()) < total_count:
        await page.wait_for_load_state("networkidle")
        results = page.locator(".result-data > a.cl-app-anchor")
        for i in range(await results.count()):
            if await results.nth(i).is_visible(timeout=1000):
                attributes[await results.nth(i).get_attribute("href")] = True
            else:
                break
        await page.evaluate(f"window.scrollTo(0, {new_height})")
        new_height += 3000

    return attributes.keys()


# Load category data from json file
#
#   filename    -> relative name of the json file
def get_json_file(filename):
    data = None
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {"active": {}, "sold": {}}
    return data


# Write the category data to json file
#
#   filename    -> relative name of the json file
#   data        -> category data to write to file
def write_to_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f)

ACTIONS = {
    "cl__update_all": update_all,
    "cl__update": update,
    "cl__update_all_p": update_all_p,
    "cl__update_p": update_p,
}
