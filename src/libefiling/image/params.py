from typing import List, TypedDict


class ImageAttribute(TypedDict):
    key: str
    value: str


class ImageConvertParam:
    def __init__(
        self,
        width: int,
        height: int,
        suffix: str | None = None,
        format: str | None = None,
        attributes: List[ImageAttribute] = [],
    ):
        self.width = width
        self.height = height
        self.suffix = suffix
        self.format = format
        self._attributes = attributes

    @property
    def attributes(self) -> dict:
        return {attr["key"]: attr["value"] for attr in self._attributes}
