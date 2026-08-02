from pathlib import Path
from typing import Iterator

from libefiling.archive.utils import generate_sha256
from libefiling.image.kind import detect_image_kind
from libefiling.image.mediatype import get_media_type
from libefiling.manifest import (
    EncodingInfo,
    ImageEntry,
    Manifest,
    Paths,
    Sources,
    Stats,
    XmlFile,
)
from libefiling.xml.kind import detect_xml_kind

from .archive.extract import extract_archive
from .charset import convert_xml_charset


def parse_archive(
    src_archive_path: str,
    src_procedure_path: str,
    output_dir: str,
):
    """parse e-filing archive and generate various outputs."""

    if not Path(src_archive_path).exists():
        raise FileNotFoundError(f"Source archive not found: {src_archive_path}")
    if not Path(src_procedure_path).exists():
        raise FileNotFoundError(f"Source procedure XML not found: {src_procedure_path}")
    output_root = Path(output_dir)
    if not output_root.exists():
        output_root.mkdir(parents=True, exist_ok=True)

    ### create output subdirectories
    p = Paths.create(output_root)

    ### extract archive to raw_dir
    extracted_files = extract_archive(src_archive_path)
    save_raw_files(extracted_files, p.raw_dir)

    ### convert charset of extracted XML files to UTF-8 and save to xml_dir
    raw_xml_files = p.raw_dir.glob("*.xml", case_sensitive=False)
    xml_files = process_xml(raw_xml_files, p.xml_dir)

    ### convert charset of procedure xml to UTF-8 and save to xml_dir
    proc_xml_path = p.xml_dir / "procedure.xml"
    xml_files.append(process_procedure_xml(Path(src_procedure_path), proc_xml_path))

    ### collect image metadata from raw files
    images = collect_image_entries(p.raw_images())

    sources = Sources.create(src_archive_path, src_procedure_path)

    ### calc stats
    stats = Stats.create(p)

    ### generate manifest
    manifest = Manifest.create(
        sources,
        xml_files,
        images,
        p.relative_to(p.root),  # paths in manifest should be relative to root
        stats,
    )
    manifest.save_as_json(p.root / "manifest.json")


def save_raw_files(
    extracted_archives: list[tuple[str, bytes]],
    raw_dir: Path,
) -> None:
    for filename, data in extracted_archives:
        output_path = raw_dir / filename
        with output_path.open("wb") as f:
            f.write(data)


def process_xml(
    raw_xml_files: Iterator[Path],
    xml_dir: Path,
) -> list[XmlFile]:
    """convert charset to UTF-8 and save to xml_dir,
    and return list of XmlFile entries.

    Args:
        raw_xml_files (Iterator[Path]): Iterator of raw XML file paths.
        xml_dir (Path): Directory to save converted XML files.

    Returns:
        list[XmlFile]: List of XmlFile entries.
    """
    xml_files = []
    for file_path in raw_xml_files:
        converted_xml_path = xml_dir / file_path.name
        convert_xml_charset(str(file_path), str(converted_xml_path))

        xml_files.append(
            XmlFile(
                filename=file_path.name,
                sha256=generate_sha256(converted_xml_path),
                encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
                kind=detect_xml_kind(file_path.name),
            )
        )

    return xml_files


def process_procedure_xml(
    src_procedure_path: Path,
    xml_path: Path,
) -> XmlFile:
    convert_xml_charset(str(src_procedure_path), str(xml_path))
    return XmlFile(
        filename=xml_path.name,
        encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
        sha256=generate_sha256(xml_path),
        kind=detect_xml_kind(xml_path.name),
    )


def collect_image_entries(image_files: list[Path]) -> list[ImageEntry]:
    return [
        ImageEntry(
            filename=image.name,
            sha256=generate_sha256(image),
            media_type=get_media_type(image.suffix),
            kind=detect_image_kind(image.name),
        )
        for image in image_files
    ]
