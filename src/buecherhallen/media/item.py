import json
import logging
from typing import Any, Optional

import requests

from buecherhallen.common.constants import BASE_URL, SOLUS_APP_ID
from buecherhallen.media.list_item import ListItem

log = logging.getLogger(__name__)


class Availability:
    def __init__(self, location: str, count: int, max_count: int, shelf: str):
        self.location = location
        self.count = count
        self.max_count = max_count
        self.shelf = shelf

    def is_available(self) -> bool:
        return self.count > 0

    def __repr__(self):
        return f"Availability({self.location}, {self.count}, {self.max_count}, {self.shelf})"


class Availabilities:
    def __init__(self, availabilities: list[Availability]):
        self.availabilities: dict[str, Availability] = \
            {availability.location: availability for availability in availabilities}

    def is_available(self, location: str) -> bool:
        return self.availabilities[location].is_available()

    def __getitem__(self, location: str) -> Availability:
        return self.availabilities[location]

    def items(self) -> list[tuple[str, Availability]]:
        return list(self.availabilities.items())

    def __repr__(self):
        return f"Availabilities({self.availabilities})"


class Item:
    video_game_format_indicators = [
        "konsolenspiel",
        "nintendo switch",
        "playstation",
        "xbox",
    ]

    video_game_genre_indicators = [
        "konsolenspiel",
    ]

    def __init__(self, item_id: str, title: str, author: Optional[str], format: Optional[str], genre: Optional[str],
                 signature: str, availabilities: Availabilities):
        self.item_id = item_id
        self.title = title
        self.author = author
        self.format = format
        self.genre = genre
        self.signature = signature
        self.availabilities = availabilities

    def is_available(self, location: str) -> bool:
        return self.availabilities.is_available(location)

    def get_clean_signature(self) -> str:
        if self.signature.startswith("1 @ "):
            return self.signature[4:]
        return self.signature

    def get_url(self) -> str:
        return f"{BASE_URL}/manifestations/{self.item_id}"

    def is_video_game(self) -> bool:
        # check 'format'
        if self.format is not None:
            format_normalized = self.format.strip().lower()

            for indicator in Item.video_game_format_indicators:
                if indicator in format_normalized:
                    return True

        # check 'Genre'
        if self.genre is not None:
            genre_normalized = self.genre.strip().lower()

            if genre_normalized in Item.video_game_genre_indicators:
                return True

        return False

    def get_icon(self) -> Optional[str]:
        if self.is_video_game():
            return "🕹"
        return None

    def __repr__(self):
        return f"Item({self.item_id}, {self.title}, {self.author}, {self.format}, {self.genre}, {self.signature}, {self.availabilities})"

    @staticmethod
    def from_json(raw: dict[str, Any]) -> 'Item':
        item_id = raw.get("recordID")
        assert item_id is not None
        title = raw.get("title")
        assert title is not None
        author = raw.get("author")
        format = raw.get("format")

        signature = ""
        genre = None
        for metadata in raw.get("mainMetadata", []):
            key = metadata.get("key")
            if key == "Signatur":
                signature = metadata.get("usableValue", "")
            if key == "Genre":
                genre = metadata.get("usableValue", None)

        copies = raw.get("copies", [])
        availabilities_list = []
        location_counts = {}
        for copy in copies:
            location_name = copy.get("location", {}).get("locationName", "Unknown Location")
            available = copy.get("available", False)
            if location_name not in location_counts:
                # 'shelf' seems to be always empty, maybe it will be used in the future
                location_counts[location_name] = {"count": 0, "max_count": 0, "shelf": copy.get("shelf", "")}
            location_counts[location_name]["max_count"] += 1
            if available:
                location_counts[location_name]["count"] += 1

        for location, counts in location_counts.items():
            availabilities_list.append(Availability(location, counts["count"], counts["max_count"], counts["shelf"]))

        availabilities = Availabilities(availabilities_list)

        return Item(item_id, title, author, format, genre, signature, availabilities)


class ItemParseError(Exception):
    pass


def retrieve_item_details(list_item: ListItem, retries: int = 0) -> Item:
    raw_item = __retrieve_raw_item_details(list_item, retries)
    item = Item.from_json(raw_item)
    print(item)
    return item


def __retrieve_raw_item_details(list_item: ListItem, retries: int) -> dict[str, Any]:
    item_id = list_item.item_id
    log.info(f"Fetching record with ID: {item_id}")
    api_url = f'{BASE_URL}/api/record?id={item_id}'
    response = requests.get(
        api_url,
        headers={'Solus-App-Id': SOLUS_APP_ID}
    )

    status_code = response.status_code
    log.debug(f"Records API response status code: {status_code}")
    if not response.ok:
        log.error(f"Failed to fetch record {item_id}: {status_code}")
        log.debug(f"Records API response content: {response.text}")
        if retries > 0:
            log.warning(f"Retrying fetch for record {item_id} ({retries} left)")
            return __retrieve_raw_item_details(list_item, retries - 1)
        raise ItemParseError(f"Failed to fetch record {item_id}: {status_code}")

    response_json = response.json()
    log.debug(f"Records API response JSON: {json.dumps(response_json, indent=2)}")

    return response_json
