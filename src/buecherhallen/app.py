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
            raise AppError(f"Login failed: {e}")

        try:
            list_items = retrieve_watchlist_items(cookies)
        except WatchlistError as e:
            raise AppError(f"Failed to retrieve watchlist: {e}")

        for item in list_items:
            print(item)

        items: list[Item] = []

        def safe_retrieve(list_item: ListItem) -> Item | None:
            try:
                return retrieve_item_details(list_item)
            except ItemParseError as ipe:
                print(f"Failed to retrieve item {list_item}: {ipe}", file=sys.stderr)
                if ipe.is_error():
                    print("Exiting due to critical error in item retrieval", file=sys.stderr)
                    raise AppError(f"Critical error in retrieval of item {list_item}: {ipe}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            items = list(filter(None, executor.map(safe_retrieve, list_items)))

        generate_website(items)
    except Exception as e:
        print(f"Error: {e}\n", file=sys.stderr)
        print(traceback.format_exc(), end='', file=sys.stderr)
        exit(1)
