import json
import logging
from typing import Any

import requests
from common.constants import BASE_URL, SOLUS_APP_ID


class WatchlistError(Exception):
    pass


def get_watchlist_item_id(item):
    if not item.has_attr('id'):
        raise WatchlistError("Watchlist item missing 'id' attribute.")
    return item['id']


def retrieve_watchlist_items(cookies: requests.cookies.RequestsCookieJar) -> Any:
    try:
        lists = retrieve_lists(cookies)

        for list in lists:
            if list.get("listName") == "Merkliste":
                watch_list_items = list.get("items", [])
                return watch_list_items

    except Exception as e:
        raise WatchlistError(f"Error retrieving watchlist items: {e}")


def retrieve_lists(cookies: requests.cookies.RequestsCookieJar) -> Any:
    logging.info("Fetching lists")

    api_url = f'{BASE_URL}/api/items?type=lists'
    response = requests.get(
        api_url,
        cookies=cookies,
        headers={'Solus-App-Id': SOLUS_APP_ID}
    )

    status_code = response.status_code
    logging.debug(f"Lists API response status code: {status_code}")
    response_json = response.json()
    logging.debug(f"Lists API response JSON: {json.dumps(response_json, indent=2)}")

    if status_code != 200:
        logging.error(f"Failed to fetch lists: {status_code}")
        return

    return response_json
