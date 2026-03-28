from typing import List

from pydantic import BaseModel, Field


class ImageAttribute(BaseModel):
    key: str
    value: str


class ImageConvertParam(BaseModel):
    width: int
    height: int
    suffix: str = ""
    format: str = ".webp"
    attributes: List[ImageAttribute] = Field(default_factory=list)
