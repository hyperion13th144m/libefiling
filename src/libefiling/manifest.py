from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Literal, Optional, get_args

from pydantic import BaseModel, Field

# -------------------------
# Generator / Document
# -------------------------


class GeneratorInfo(BaseModel):
    name: str = Field(..., examples=["libefiling"])
    version: str = Field(..., examples=["0.1.0"])
    created_at: datetime


class Source(BaseModel):
    filename: str
    sha256: str
    byte_size: int
    task: str
    kind: str
    extension: str

    @classmethod
    def create(cls, file_path: str, sha256: str) -> Source:
        """Create Source from file path

        Args:
            file_path (str): file path
        """
        filename = Path(file_path).name
        byte_size = Path(file_path).stat().st_size
        if len(filename) == 63:
            task = filename[56 : 56 + 1]
            kind_code = filename[57 : 57 + 2]
        else:
            task = "X"  # X means unknown
            kind_code = "XX"  # XX means unknown
        extension = Path(file_path).suffix.upper()
        return cls(
            filename=filename,
            sha256=sha256,
            byte_size=byte_size,
            task=task,
            kind=kind_code,
            extension=extension,
        )


class DocumentInfo(BaseModel):
    doc_id: str
    sources: List[Source]


# -------------------------
# Paths
# -------------------------


class Paths(BaseModel):
    root: str = "."
    raw_dir: str = "raw"
    xml_dir: str = "xml"
    images_dir: str = "images"
    ocr_dir: str = "ocr"


# -------------------------
# XML
# -------------------------


class EncodingInfo(BaseModel):
    detected: Optional[str] = None
    normalized_to: str = "UTF-8"
    had_bom: bool = False


class XmlFile(BaseModel):
    filename: str
    original_filename: Optional[str] = None
    sha256: str
    encoding: EncodingInfo
    media_type: str = "application/xml"


# -------------------------
# Images / OCR
# -------------------------


class ImageAttributes(BaseModel):
    key: str
    value: str


class DerivedImage(BaseModel):
    filename: str
    media_type: str = "image/webp"
    width: int
    height: int
    sha256: str
    attributes: List[ImageAttributes] = []


class OcrInfo(BaseModel):
    filename: str
    format: str = "text/plain"
    sha256: str
    lang: Optional[str] = "jpn"
    engine: Optional[str] = None
    engine_version: Optional[str] = None
    confidence_avg: Optional[float] = None


class ImageEntry(BaseModel):
    filename: str
    sha256: str
    media_type: str = "image/tiff"
    kind: Literal[
        "chemical-formulas", "figures", "equations", "tables", "other-images", "unknown"
    ]
    derived: List[DerivedImage] = []
    ocr: Optional[OcrInfo] = None


# -------------------------
# Stats
# -------------------------


class Stats(BaseModel):
    xml_count: int
    image_original_count: int
    image_derived_count: int
    ocr_result_count: int


# -------------------------
# Manifest (root)
# -------------------------


class Manifest(BaseModel):
    manifest_version: str = "1.0.0"
    generator: GeneratorInfo
    document: DocumentInfo
    paths: Paths = Paths()
    xml_files: List[XmlFile] = []
    images: List[ImageEntry] = []
    stats: Stats
