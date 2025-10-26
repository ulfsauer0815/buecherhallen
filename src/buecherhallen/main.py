import concurrent.futures
import logging
import sys
import traceback

from auth.credentials import retrieve_credentials
from auth.login import login, LoginError
from common.options import retrieve_options
from media.item import retrieve_item_details, Item, ItemParseError
from media.watchlist import retrieve_watchlist_items, WatchlistError
from ui.site import generate_website


class MainError(Exception):
    pass


def main():
    try:
        credentials = retrieve_credentials()
        options = retrieve_options()
        try:
            cookies = login(credentials, options.cache_cookies)
        except LoginError as e:
            raise MainError(f"Login failed: {e}")

        try:
            item_ids = retrieve_watchlist_items(cookies)
        except WatchlistError as e:
            raise MainError(f"Failed to retrieve watchlist: {e}")
        print(item_ids)

        exit(0)  # Temporary exit to skip further processing

        items: list[Item] = []

        def safe_retrieve(item_id):
            try:
                return retrieve_item_details(item_id)
            except ItemParseError as e:
                print(f"Failed to retrieve item {item_id}: {e}", file=sys.stderr)
                if e.is_error():
                    print("Exiting due to critical error in item retrieval", file=sys.stderr)
                    raise MainError(f"Critical error in retrieval of item {item_id}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            items = list(filter(None, executor.map(safe_retrieve, item_ids)))
        generate_website(items)
    except Exception as e:
        print(f"Error: {e}\n", file=sys.stderr)
        print(traceback.format_exc(), end='', file=sys.stderr)
        exit(1)


logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    main()
