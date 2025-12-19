from dataclasses import dataclass
from typing import List


@dataclass
class ImageAttribute:
    key: str
    value: str


@dataclass
class ImageConvertParam:
    suffix: str | None
    format: str | None
    width: int
    height: int
    attributes: List[ImageAttribute]
