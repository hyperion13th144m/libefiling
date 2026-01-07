from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# -------------------------
# Generator / Document
# -------------------------


class GeneratorInfo(BaseModel):
    name: str = Field(..., examples=["libefiling"])
    version: str = Field(..., examples=["0.1.0"])
    created_at: datetime


class ArchiveSource(BaseModel):
    archive_filename: str
    archive_sha256: str
    byte_size: int
    task: Literal["A", "N", "D", "I", "O", "P", "S"]
    kind: Literal["AS", "AA", "NF", "ER"]
    extension: str


class ProcedureSource(BaseModel):
    procedure_filename: str
    procedure_sha256: str
    byte_size: int


class DocumentInfo(BaseModel):
    doc_id: str
    source: ArchiveSource
    procedure_source: ProcedureSource


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
    path: str
    original_path: Optional[str] = None
    sha256: str
    encoding: EncodingInfo
    media_type: str = "application/xml"
    role_hint: str = "unknown"


# -------------------------
# Images / OCR
# -------------------------


class ImageAttributes(BaseModel):
    key: str
    value: str


class DerivedImage(BaseModel):
    path: str
    media_type: str = "image/webp"
    width: int
    height: int
    sha256: str
    attributes: List[ImageAttributes] = []


class OriginalImage(BaseModel):
    path: str
    sha256: str
    media_type: str = "image/tiff"


class OcrInfo(BaseModel):
    path: str
    format: str = "text/plain"
    sha256: str
    lang: Optional[str] = "jpn"
    engine: Optional[str] = None
    engine_version: Optional[str] = None
    confidence_avg: Optional[float] = None


class ImageEntry(BaseModel):
    id: str
    kind: Literal["chemistry", "figure", "math", "table", "image", "unknown"]
    original: OriginalImage
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
