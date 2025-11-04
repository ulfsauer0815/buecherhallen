import concurrent.futures
import logging
import sys
import traceback

from auth.credentials import retrieve_credentials
from auth.login import login, LoginError
from common.options import retrieve_options
from media.item import retrieve_item_details, Item, ItemParseError
from media.list_item import ListItem
from media.watchlist import retrieve_watchlist_items, WatchlistError
from ui.site import generate_website

logger = logging.getLogger(__name__)


class AppError(Exception):
    pass


def run():
    try:
        credentials = retrieve_credentials()
        options = retrieve_options()
        try:
            cookies = login(credentials, options.cache_cookies, options.headless)
        except LoginError as e:
            raise AppError(f"Login failed: {e}") from e

        try:
            list_items = retrieve_watchlist_items(cookies)
        except WatchlistError as e:
            raise AppError(f"Failed to retrieve watchlist: {e}") from e

        for item in list_items:
            print(item)

        items: list[Item] = []

        def safe_retrieve(list_item: ListItem) -> Item:
            try:
                return retrieve_item_details(list_item, options.retries)
            except ItemParseError as ipe:
                raise AppError(f"Failed to retrieve item {list_item}: {ipe}") from ipe

        with concurrent.futures.ThreadPoolExecutor(max_workers=options.workers) as executor:
            items = list(filter(None, executor.map(safe_retrieve, list_items)))
        items.sort(key=lambda x: x.signature)

        generate_website(items)
    except Exception as e:
        print(traceback.format_exc(), end='', file=sys.stderr)
        print(f"\nError: {e}", file=sys.stderr)
        exit(1)
