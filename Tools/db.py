"""
format:
_id: Vars.DB_NAME
user_id: {
     "subs": {
        "ck": [],
        "as": [],
        ...
     },
     "setting": {
        "file_name": "",
        "caption": "",
        ...
     }
}
"""

import asyncio
from loguru import logger
from pymongo import MongoClient
from bot import Vars, remove_site_sf
import time
import re

client = MongoClient(Vars.DB_URL)
db = client[Vars.DB_NAME]
users = db["users"]
acollection = db['premium']

# load DB documents (these are single-doc stores keyed by _id == Vars.DB_NAME)
uts = users.find_one({"_id": Vars.DB_NAME})
if not uts:
    uts = {'_id': Vars.DB_NAME}
    users.insert_one(uts)

pts = acollection.find_one({"_id": Vars.DB_NAME})
if not pts:
    pts = {'_id': Vars.DB_NAME}
    acollection.insert_one(pts)


def sync(name=None, type=None):
    """Persist uts to DB"""
    users.replace_one({'_id': Vars.DB_NAME}, uts)


def premuim_sync():
    """Persist pts to DB"""
    acollection.replace_one({'_id': Vars.DB_NAME}, pts)


def get_episode_number(text):
    """Extract episode/chapter number from text"""
    patterns = [
        r"Volume\s+(\d+)\s+Chapter\s+(\d+(?:\.\d+)?)",
        r"Chapter\s+(\d+(?:\.\d+)?)",
        r"Chapter\s+(\d+)\s*-\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)"
    ]

    text = str(text)
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # return the last matched numeric group that makes sense
            for g in match.groups():
                if g:
                    return g
    return None


def ensure_user(user_id):
    """Make sure user exists in uts with required keys"""
    user_id = str(user_id)
    if user_id not in uts:
        uts[user_id] = {"subs": {}, "setting": {}}
        sync()

    if "subs" not in uts[user_id]:
        uts[user_id]["subs"] = {}
        sync()

    if "setting" not in uts[user_id]:
        uts[user_id]["setting"] = {}
        sync()


async def add_premium(user_id, time_limit_days):
    user_id = str(user_id)
    expiration_timestamp = int(time.time()) + int(time_limit_days) * 24 * 60 * 60
    premium_data = {"expiration_timestamp": expiration_timestamp}
    pts[user_id] = premium_data
    premuim_sync()


async def remove_premium(user_id):
    user_id = str(user_id)
    if user_id in pts:
        del pts[user_id]
        premuim_sync()


async def remove_expired_users():
    current_timestamp = int(time.time())
    expired_users = [user for user, data in pts.items() if data.get("expiration_timestamp", 0) < current_timestamp]
    for expired_user in expired_users:
        try:
            await remove_premium(expired_user)
        except Exception:
            # ignore single-user failures
            pass


async def get_all_premuim():
    """Yields (user_id, data) for premium users"""
    for user_id, data in pts.items():
        # skip the document id key if accidentally present
        if user_id == "_id":
            continue
        yield user_id, data


async def premium_user(user_id):
    user_id = str(user_id)
    return pts.get(user_id)


def get_users(user_id=None):
    """
    If user_id is provided -> return the user dict from uts (or None)
    If not provided -> return list of all numeric user ids (ints) present in uts (excluding '_id')
    """
    if user_id is not None:
        return uts.get(str(user_id))
    # return list of user ids as ints (skip internal _id)
    keys = [k for k in uts.keys() if k != "_id"]
    ids = []
    for k in keys:
        try:
            ids.append(int(k))
        except Exception:
            # keep non-int keys out
            continue
    return ids


async def add_sub(user_id, rdata, web: str, chapter=None):
    user_id = str(user_id)
    ensure_user(user_id)

    if web not in uts[user_id]["subs"]:
        uts[user_id]["subs"][web] = []
        sync()

    # rdata is expected to have load_to_dict()
    data = rdata.load_to_dict()
    # avoid duplicates (both dict and string forms)
    if data not in uts[user_id]["subs"][web]:
        uts[user_id]["subs"][web].append(data)
        sync()


def _url_equals(entry, manga_url):
    """
    Helper: compare an entry (which may be a str or dict) to manga_url
    """
    if isinstance(entry, str):
        return entry == manga_url
    if isinstance(entry, dict):
        return entry.get("url") == manga_url
    return False


def get_subs(user_id, manga_url=None, web=None):
    """
    Return either:
     - list of subscriptions for the user (flattened)
     - True/False (or None) when checking existence of a specific manga_url
    Supports mixed DB formats: subs may contain strings or dicts, and user_info may be dict or legacy structures.
    """
    user_id = str(user_id)
    ensure_user(user_id)

    user_info = get_users(user_id)
    if not user_info:
        return []  # no subscriptions

    # ensure structure is dict-like: user_info should be uts[user_id]
    # If get_users returned a list earlier (wrong usage), convert
    if not isinstance(user_info, dict):
        # fallback - attempt to get from uts
        user_info = uts.get(user_id, {})

    subs_list = []

    subs = user_info.get("subs", {})
    # if subs accidentally stored as a list -> treat as list of urls
    if isinstance(subs, list):
        if manga_url:
            return any(_url_equals(s, manga_url) for s in subs)
        subs_list.extend(subs)
        return subs_list

    # subs is expected to be a dict of site_sf -> list
    if web:
        web_list = subs.get(web, [])
        if manga_url:
            return any(_url_equals(entry, manga_url) for entry in web_list)
        subs_list.extend(web_list)
        return subs_list

    # no specific web provided -> gather all
    for site_key, site_subs in subs.items():
        # site_subs may be list or dict; handle only lists
        if isinstance(site_subs, list):
            if manga_url:
                if any(_url_equals(entry, manga_url) for entry in site_subs):
                    return True
            else:
                subs_list.extend(site_subs)
        elif isinstance(site_subs, dict):
            # if someone stored dict per sub accidentally, try to extract values
            for entry in site_subs.values():
                if isinstance(entry, list):
                    if manga_url:
                        if any(_url_equals(e, manga_url) for e in entry):
                            return True
                    else:
                        subs_list.extend(entry)
    if manga_url:
        return None if not subs_list else any(_url_equals(s, manga_url) for s in subs_list)
    return subs_list


async def delete_sub(user_id, manga_url=None, web=None):
    """
    Delete subscribed manga for a user.
    If manga_url is None and web is None -> delete all subs for user.
    If manga_url is None and web provided -> delete all subs for that web.
    If manga_url provided -> delete that specific manga from web or across all webs.
    """
    user_id = str(user_id)
    ensure_user(user_id)

    user_info = uts.get(user_id, {})
    subs = user_info.get("subs", {})

    # if subs stored as list -> convert to dict with 'unknown' key to safely remove entries
    if isinstance(subs, list):
        # convert and save
        new_subs = {}
        for url in subs:
            site_sf = next((sf for sf in remove_site_sf if sf in url), "unknown")
            new_subs.setdefault(site_sf, []).append({"url": url} if isinstance(url, str) else url)
        uts[user_id]["subs"] = new_subs
        sync()
        subs = new_subs

    # delete all subs for user
    if not web and not manga_url:
        uts[user_id]["subs"] = {}
        sync()
        return

    # delete all subs for a specific web
    if web and not manga_url:
        if web in uts[user_id]["subs"]:
            del uts[user_id]["subs"][web]
            sync()
        return

    # delete a specific manga_url for a web (or across all webs)
    if manga_url and web:
        web_subs = uts[user_id]["subs"].get(web, [])
        # remove matching entries (handle strings and dicts)
        remaining = [e for e in web_subs if not _url_equals(e, manga_url)]
        if remaining:
            uts[user_id]["subs"][web] = remaining
        else:
            uts[user_id]["subs"].pop(web, None)
        sync()
        return

    if manga_url and not web:
        # remove across all webs
        for website in list(uts[user_id]["subs"].keys()):
            site_list = uts[user_id]["subs"].get(website, [])
            remaining = [e for e in site_list if not _url_equals(e, manga_url)]
            if remaining:
                uts[user_id]["subs"][website] = remaining
            else:
                uts[user_id]["subs"].pop(website, None)
        sync()
        return


async def get_all_subs():
    """
    Yields each URL entry in format:
    yield user_id, website_sf, sub
    Supports mixed DB formats (list or dict).
    Also performs an automatic conversion for list-based legacy subs into dict format
    so next runs will be consistent.
    """
    # collect user ids: prefer premium pts keys first, then uts keys
    users_list = [user_id for user_id, _ in pts.items() if user_id != "_id"]
    users_list += [user_id for user_id, _ in uts.items() if user_id != "_id" and user_id not in users_list]

    for user_id in users_list:
        # skip if no user data in uts
        data = uts.get(user_id)
        if not data:
            continue

        subs = data.get("subs")
        if subs is None:
            continue

        # If subs stored as a list -> convert to dict and save (migration)
        if isinstance(subs, list):
            new_subs = {}
            for url in subs:
                # detect site short form by matching remove_site_sf substrings in url
                site_sf = next((sf for sf in remove_site_sf if sf in (url or "")), "unknown")
                new_subs.setdefault(site_sf, []).append({"url": url} if isinstance(url, str) else url)

            uts[user_id]["subs"] = new_subs
            sync()
            subs = new_subs

        # Now subs expected to be a dict
        if isinstance(subs, dict):
            for website_sf, site_subs in subs.items():
                # remove sites that are in the banned list
                if website_sf in remove_site_sf:
                    # delete_sub will sync
                    await delete_sub(user_id, web=website_sf)
                    continue

                # site_subs should be a list
                if isinstance(site_subs, list):
                    for sub in site_subs:
                        yield user_id, website_sf, sub
                else:
                    # if someone stored a single dict, yield it
                    if isinstance(site_subs, dict):
                        yield user_id, website_sf, site_subs
                    else:
                        # ignore invalid formats
                        continue
        else:
            # unknown format - try to yield items if possible
            if isinstance(subs, list):
                for sub in subs:
                    yield user_id, None, sub
            else:
                continue


async def save_lastest_chapter(data: dict, user_id: str, web_sf: str):
    """
    Update the latest chapter for subscribed manga
    """
    try:
        main_keys = {"title", "url", "lastest_chapter"}
        user_data = uts.get(user_id, {})
        user_subs = user_data.get('subs', {})
        subscribed_manga = user_subs.get(web_sf, [])

        if not subscribed_manga:
            return

        # sanitize data to only include allowed keys
        data_clean = {k: data[k] for k in list(data.keys()) if k in main_keys}

        for index, manga_data in enumerate(subscribed_manga):
            # manga_data might be str or dict
            manga_url = manga_data.get('url') if isinstance(manga_data, dict) else manga_data
            title_matches = (isinstance(manga_data, dict) and manga_data.get("title") == data_clean.get("title"))
            url_matches = (data_clean.get("url") == manga_url)

            if url_matches or title_matches:
                # replace entry with cleaned data (keep as dict)
                uts[user_id]['subs'][web_sf][index] = data_clean
                sync()
                await asyncio.sleep(3)
                break

    except Exception as err:
        logger.exception(f"Error at Save Lastest Chapter: {err}")
     
