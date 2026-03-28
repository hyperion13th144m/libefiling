from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field

from libefiling.archive.utils import generate_sha256
from libefiling.image.kind import IMAGE_KIND
from libefiling.xml.kind import XML_KIND

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
    def create(cls, file_path: str | Path) -> Source:
        """Create Source from file path

        Args:
            file_path (str | Path): file path
        """
        filename = Path(file_path).name
        sha256 = generate_sha256(file_path)
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

    def get_document_code(self) -> str:
        """Get document code from archive file name

        Args:
        Returns:
            str: document code (e.g. A163) or None if not found
        """
        if len(self.filename) < 29:
            return "UNKNOWN"
        else:
            return self.filename[19 : 19 + 9].replace("_", "").strip()


class Sources(BaseModel):
    document_code: str
    archive: Source
    procedure: Source

    def save_as_xml(self, xml_path: str) -> None:
        """Save Sources as XML file

        Args:
            xml_path (str): XML file path to save
        """
        root = ET.Element("sources", attrib={"document-code": self.document_code})
        for i, source in enumerate([self.archive, self.procedure]):
            ET.SubElement(
                root,
                "archive" if i == 0 else "procedure",
                attrib={
                    "filename": source.filename,
                    "sha256": source.sha256,
                    "byte-size": str(source.byte_size),
                    "task": source.task,
                    "kind": source.kind,
                    "extension": source.extension,
                },
            )
        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    def to_xml_file(self, xml_path: str) -> XmlFile:
        return XmlFile(
            filename=Path(xml_path).name,
            original_filename=None,
            sha256=generate_sha256(xml_path),
            encoding=EncodingInfo(detected="UTF-8", normalized_to="UTF-8"),
            kind="source",
        )


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
    kind: XML_KIND


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
    kind: IMAGE_KIND
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
    sources: Sources
    paths: Paths = Paths()
    xml_files: List[XmlFile] = []
    images: List[ImageEntry] = []
    stats: Stats
