import json
import logging
from typing import Any

import requests
from buecherhallen.media.list_item import ListItem
from common.constants import BASE_URL, SOLUS_APP_ID

log = logging.getLogger(__name__)


class WatchlistError(Exception):
    pass


def retrieve_watchlist_items(cookies: requests.cookies.RequestsCookieJar) -> Any:
    try:
        raw_items = __retrieve_watchlist_raw_items(cookies)
        return [ListItem.from_json(raw_item) for raw_item in raw_items]
    except Exception as e:
        raise WatchlistError(f"Error retrieving watchlist items: {e}")


def __retrieve_watchlist_raw_items(cookies: requests.cookies.RequestsCookieJar) -> Any:
    lists = __retrieve_lists(cookies)

    for list in lists:
        if list.get("listName") == "Merkliste":
            watch_list_items = list.get("items", [])
            return watch_list_items


def __retrieve_lists(cookies: requests.cookies.RequestsCookieJar) -> Any:
    log.info("Fetching lists")

    api_url = f'{BASE_URL}/api/items?type=lists'
    response = requests.get(
        api_url,
        cookies=cookies,
        headers={'Solus-App-Id': SOLUS_APP_ID}
    )

    status_code = response.status_code
    log.debug(f"Lists API response status code: {status_code}")
    response_json = response.json()
    log.debug(f"Lists API response JSON: {json.dumps(response_json, indent=2)}")

    if status_code != 200:
        log.error(f"Failed to fetch lists: {status_code}")
        return

    return response_json
