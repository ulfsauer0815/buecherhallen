from typing import Any


class ListItem:
    def __init__(self, id, title, author):
        self.id = id
        self.title = title
        self.author = author

    def __repr__(self):
        return f"ListItem({self.id}, {self.title}, {self.author})"

    @staticmethod
    def from_json(raw: Any) -> 'ListItem':
        id = raw.get("id")
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

        return ListItem(id, title, author)
