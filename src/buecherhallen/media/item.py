import json
import logging
from enum import Enum
from typing import Any

import requests
from common.constants import BASE_URL, SOLUS_APP_ID
from media.list_item import ListItem

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
    def __init__(self, item_id, title, author, signature, availabilities):
        self.item_id = item_id
        self.title = title
        self.author = author
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

    def __repr__(self):
        return f"Item({self.item_id}, {self.title}, {self.author}, {self.signature}, {self.availabilities})"

    @staticmethod
    def from_json(raw: Any) -> 'Item':
        item_id = raw.get("recordID")
        title = raw.get("title")
        author = raw.get("author")

        signature = ""
        for metadata in raw.get("mainMetadata", []):
            if metadata.get("key") == "Signatur":
                signature = metadata.get("usableValue", "")
                break

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

        return Item(item_id, title, author, signature, availabilities)


class Severity(Enum):
    WARN = "WARN"
    ERROR = "ERROR"


class ItemParseError(Exception):
    def __init__(self, message: str, severity: Severity = Severity.ERROR):
        super().__init__(message)
        self.severity = severity
        self.message = message

    def __str__(self):
        return f"[{self.severity.value}] {self.message}"

    def is_error(self) -> bool:
        return self.severity == Severity.ERROR

    def is_warn(self) -> bool:
        return self.severity == Severity.WARN


def retrieve_item_details(list_item: ListItem, retries: int = 0) -> Item:
    raw_item = __retrieve_raw_item_details(list_item, retries)
    item = Item.from_json(raw_item)
    print(item)
    return item


def __retrieve_raw_item_details(list_item: ListItem, retries: int) -> Item:
    item_id = list_item.item_id
    log.info(f"Fetching record with ID: {item_id}")
    api_url = f'{BASE_URL}/api/record?id={item_id}a'
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
        raise ItemParseError(f"Failed to fetch record {item_id}: {status_code}", Severity.ERROR)

    response_json = response.json()
    log.debug(f"Records API response JSON: {json.dumps(response_json, indent=2)}")

    return response_json
