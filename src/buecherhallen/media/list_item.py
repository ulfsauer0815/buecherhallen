from typing import Any


class ListItem:
    def __init__(self, item_id, title, author):
        self.item_id = item_id
        self.title = title
        self.author = author

    def __repr__(self):
        return f"ListItem({self.item_id}, {self.title}, {self.author})"

    @staticmethod
    def from_json(raw: Any) -> 'ListItem':
        item_id = raw.get("id")
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

        return ListItem(item_id, title, author)
