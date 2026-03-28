from __future__ import annotations

from datetime import datetime
from importlib.metadata import version as get_version
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

    @classmethod
    def create(cls, archive_path: str | Path, procedure_path: str | Path) -> Sources:
        """Create Sources from archive and procedure file paths

        Args:
            archive_path (str | Path): archive file path
            procedure_path (str | Path): procedure file path
        """
        archive = Source.create(archive_path)
        procedure = Source.create(procedure_path)
        document_code = archive.get_document_code()
        return cls(document_code=document_code, archive=archive, procedure=procedure)

    def save_as_xml(self, xml_path: str | Path) -> None:
        """Save Sources as XML file

        Args:
            xml_path (str | Path): XML file path to save
        """
        xml_path = Path(xml_path)
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


# -------------------------
# Paths
# -------------------------


class Paths(BaseModel):
    root: Path = Path(".")
    raw_dir: Path = Path("raw")
    xml_dir: Path = Path("xml")
    images_dir: Path = Path("images")
    ocr_dir: Path = Path("ocr")

    @classmethod
    def create(cls, root: str | Path = ".") -> Paths:
        root = Path(root)
        raw_dir = root / "raw"
        xml_dir = root / "xml"
        images_dir = root / "images"
        ocr_dir = root / "ocr"
        for d in [raw_dir, xml_dir, images_dir, ocr_dir]:
            d.mkdir(parents=True, exist_ok=True)

        return cls(
            root=root,
            raw_dir=raw_dir,
            xml_dir=xml_dir,
            images_dir=images_dir,
            ocr_dir=ocr_dir,
        )

    def relative_to(self, base: str | Path) -> Paths:
        base = Path(base)
        return Paths(
            root=self.root.relative_to(base),
            raw_dir=self.raw_dir.relative_to(base),
            xml_dir=self.xml_dir.relative_to(base),
            images_dir=self.images_dir.relative_to(base),
            ocr_dir=self.ocr_dir.relative_to(base),
        )

    def raw_images(self) -> List[Path]:
        return list(self.raw_dir.glob("*.tif", case_sensitive=False)) + list(
            self.raw_dir.glob("*.jpg", case_sensitive=False)
        )


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

    @classmethod
    def to_xml_file(cls, xml_path: str | Path, kind: XML_KIND) -> XmlFile:
        return cls(
            filename=Path(xml_path).name,
            original_filename=None,
            sha256=generate_sha256(xml_path),
            encoding=EncodingInfo(detected="UTF-8", normalized_to="UTF-8"),
            kind=kind,
        )


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
    attributes: List[ImageAttributes] = Field(default_factory=list)


class OcrInfo(BaseModel):
    filename: str
    format: str = "text/plain"
    sha256: str
    lang: Optional[str] = "jpn"

    def add_ocr_text(self, ocr_text: str) -> None:
        self._ocr_text = ocr_text

    def get_ocr_text(self) -> Optional[str]:
        if hasattr(self, "_ocr_text") and len(self._ocr_text) > 0:
            return self._ocr_text
        return None


class ImageEntry(BaseModel):
    filename: str
    sha256: str
    media_type: str = "image/tiff"
    kind: IMAGE_KIND
    derived: List[DerivedImage] = Field(default_factory=list)
    ocr: Optional[OcrInfo] = None

    @staticmethod
    def save_as_xml(entries: List[ImageEntry], xml_path: str | Path) -> None:
        """Save Sources as XML file

        Args:
            xml_path (str | Path): XML file path to save
        """
        xml_path = Path(xml_path)
        root = ET.Element("images")
        for entry in entries:
            image_elem = ET.SubElement(
                root,
                "image",
                attrib={
                    "filename": entry.filename,
                    "sha256": entry.sha256,
                    "media-type": entry.media_type,
                    "kind": entry.kind,
                },
            )
            for derived in entry.derived:
                derived_elem = ET.SubElement(
                    image_elem,
                    "derived",
                    attrib={
                        "filename": derived.filename,
                        "sha256": derived.sha256,
                        "media-type": derived.media_type,
                        "width": str(derived.width),
                        "height": str(derived.height),
                    },
                )
                for attr in derived.attributes:
                    ET.SubElement(
                        derived_elem,
                        "attribute",
                        attrib={"key": attr.key, "value": attr.value},
                    )
            if entry.ocr is not None:
                ocr_elem = ET.SubElement(
                    image_elem,
                    "ocr",
                    attrib={
                        "filename": entry.ocr.filename,
                        "sha256": entry.ocr.sha256,
                        "format": entry.ocr.format,
                        "lang": entry.ocr.lang or "",
                    },
                )
                t = entry.ocr.get_ocr_text()
                if t is not None:
                    ocr_elem.text = t

        tree = ET.ElementTree(root)
        tree.write(xml_path, encoding="utf-8", xml_declaration=True)


# -------------------------
# Stats
# -------------------------


class Stats(BaseModel):
    xml_count: int
    image_original_count: int
    image_derived_count: int
    ocr_result_count: int

    @staticmethod
    def _count_files_by_suffix(directory: Path, suffixes: set[str]) -> int:
        lowered = {suffix.lower() for suffix in suffixes}
        return sum(
            1
            for file_path in directory.rglob("*")
            if file_path.is_file() and file_path.suffix.lower() in lowered
        )

    @classmethod
    def create(cls, path: Paths) -> "Stats":
        xml_count = cls._count_files_by_suffix(path.xml_dir, {".xml"})
        image_original_count = cls._count_files_by_suffix(
            path.raw_dir,
            {".tif", ".tiff", ".jpg", ".jpeg"},
        )
        image_derived_count = cls._count_files_by_suffix(path.images_dir, {".webp"})
        ocr_result_count = cls._count_files_by_suffix(path.ocr_dir, {".txt"})
        return cls(
            xml_count=xml_count,
            image_original_count=image_original_count,
            image_derived_count=image_derived_count,
            ocr_result_count=ocr_result_count,
        )


# -------------------------
# Manifest (root)
# -------------------------


class Manifest(BaseModel):
    manifest_version: str = "1.0.0"
    generator: GeneratorInfo
    sources: Sources
    paths: Paths = Field(default_factory=Paths)
    xml_files: List[XmlFile] = Field(default_factory=list)
    images: List[ImageEntry] = Field(default_factory=list)
    stats: Stats

    @classmethod
    def create(
        cls,
        sources: Sources,
        xml_files: list[XmlFile],
        images: list[ImageEntry],
        paths: Paths,
        stats: Stats,
    ) -> Manifest:
        return cls(
            generator=GeneratorInfo(
                name="libefiling",
                version=get_version("libefiling"),
                created_at=datetime.now(),
            ),
            sources=sources,
            paths=paths,
            xml_files=xml_files,
            images=images,
            stats=stats,
        )

    def save_as_json(self, json_path: str | Path) -> None:
        json_path = Path(json_path)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=4, ensure_ascii=False))
