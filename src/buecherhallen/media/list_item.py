from typing import Any, Optional

from buecherhallen.common.constants import BASE_URL


class ListItem:
    def __init__(self, item_id: str, source: str, title: str, author: Optional[str]):
        self.item_id = item_id
        self.source = source
        self.title = title
        self.author = author

    def __repr__(self):
        return f"ListItem({self.item_id}, {self.title}, {self.author})"

    def get_url(self) -> str:
        return f"{BASE_URL}/manifestations/{self.item_id}?source={self.source}"

    @staticmethod
    def from_json(raw: dict[str, Any]) -> 'ListItem':
        item_id = raw.get("id")
        assert item_id is not None
        source = raw.get("source")
        assert source is not None
        title = None
        author = None

        additional_metadata = raw.get("additionalMetaData", [])
        for meta in additional_metadata:
            key = meta.get("key")
            value = meta.get("value")
            if key == "title":
                title = value
            elif key == "author":
                author = value

        assert title is not None

        return ListItem(item_id, source, title, author)
