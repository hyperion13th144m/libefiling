import os
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path
from typing import Iterable, Iterator, List

from libefiling.archive.utils import generate_sha256
from libefiling.html.builder import build_appb_xml, build_jpbibl_xml
from libefiling.html.parser import parse as parse_html_text
from libefiling.html.reader import find_htm_file, read_htm
from libefiling.image.kind import OCR_TARGET, detect_image_kind
from libefiling.image.mediatype import get_media_type
from libefiling.manifest import (
    DerivedImage,
    EncodingInfo,
    ImageAttributes,
    ImageEntry,
    Manifest,
    OcrInfo,
    Paths,
    Source,
    Sources,
    Stats,
    XmlFile,
)
from libefiling.xml.kind import detect_xml_kind

from .archive.extract import extract_archive
from .charset import convert_xml_charset
from .default_config import defaultImageParams
from .image.convert import convert_prepared, load_image
from .image.ocr import guess_language_by_filename, ocr_image
from .image.params import ImageConvertParam


def parse_archive(
    src_archive_path: str,
    src_procedure_path: str,
    output_dir: str,
    image_params: list[ImageConvertParam] | None = None,
    ocr_target: List[OCR_TARGET] | None = None,
    image_max_workers: int | None = None,
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

    ### guess language
    lang = guess_language_by_filename(str(p.xml_dir))

    params = image_params if image_params is not None else defaultImageParams

    ### process images
    images = process_images(
        p.raw_images(),
        p.images_dir,
        p.ocr_dir,
        params,
        lang,
        ocr_target,
        max_workers=image_max_workers,
    )

    ### generate images-information.xml
    image_info_xml_path = p.xml_dir / "images-information.xml"
    ImageEntry.save_as_xml(images, image_info_xml_path)
    xml_files.append(
        XmlFile.to_xml_file(image_info_xml_path, kind="images-information")
    )

    ### generate sources.xml
    sources = Sources.create(src_archive_path, src_procedure_path)
    sources_xml_path = p.xml_dir / "sources.xml"
    sources.save_as_xml(sources_xml_path)
    xml_files.append(XmlFile.to_xml_file(sources_xml_path, kind="source"))

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


def process_images(
    image_files: Iterable[Path],
    images_dir: Path,
    ocr_dir: Path,
    image_params: list[ImageConvertParam],
    lang: str,
    ocr_target: List[OCR_TARGET] | None = None,
    max_workers: int | None = None,
) -> list[ImageEntry]:
    image_list = list(image_files)
    if not image_list:
        return []

    workers = _resolve_worker_count(max_workers)
    if workers <= 1 or len(image_list) == 1:
        return [
            _process_single_image(
                image, images_dir, ocr_dir, image_params, lang, ocr_target
            )
            for image in image_list
        ]

    with ThreadPoolExecutor(max_workers=workers) as executor:
        process_one = partial(
            _process_single_image,
            images_dir=images_dir,
            ocr_dir=ocr_dir,
            image_params=image_params,
            lang=lang,
            ocr_target=ocr_target,
        )
        return list(
            executor.map(process_one, image_list)
        )


def _resolve_worker_count(max_workers: int | None) -> int:
    if max_workers is None:
        return 1
    if max_workers == 0:
        return min(32, os.cpu_count() or 1)
    return max(1, max_workers)


def _process_single_image(
    image: Path,
    images_dir: Path,
    ocr_dir: Path,
    image_params: list[ImageConvertParam],
    lang: str,
    ocr_target: List[OCR_TARGET] | None,
) -> ImageEntry:
    derived_images = convert_images(image, images_dir, image_params)
    image_kind = detect_image_kind(image.name)

    if ocr_target is not None:
        if image_kind in ocr_target or "ALL" in ocr_target:
            ocr = get_ocr_info(image, ocr_dir, lang)
        else:
            ocr = None
    else:
        ocr = None

    return ImageEntry(
        filename=image.name,
        sha256=generate_sha256(image),
        media_type=get_media_type(image.suffix),
        kind=image_kind,
        derived=derived_images,
        ocr=ocr,
    )


def convert_images(
    image: Path, images_dir: Path, image_params: list[ImageConvertParam]
) -> list[DerivedImage]:
    derived_images = []
    prepared_image = load_image(image)
    for param in image_params:
        suffix = param.suffix if param.suffix is not None else ""
        format = param.format if param.format is not None else ".webp"
        new = Path(image).stem + suffix + format
        derived_image_path = images_dir / new

        ### convert image and save to images_dir
        converted_image = convert_prepared(prepared_image, param.width, param.height)
        converted_image.save(derived_image_path)
        new_width, new_height = converted_image.width, converted_image.height

        ### prepare DerivedImage entries
        attributes = [
            ImageAttributes(key=attr.key, value=attr.value) for attr in param.attributes
        ]
        derived_images.append(
            DerivedImage(
                filename=new,
                sha256=generate_sha256(derived_image_path),
                width=new_width,
                height=new_height,
                attributes=attributes,
                media_type=get_media_type(Path(new).suffix or ""),
            )
        )
    return derived_images


def get_ocr_info(image: Path, ocr_dir: Path, lang: str) -> OcrInfo:
    ocr_text = ocr_image(str(image), lang=lang)
    ocr_text = sanitize_text(ocr_text)
    ocr_path = ocr_dir / (Path(image).stem + ".txt")
    with open(ocr_path, "w", encoding="utf-8") as f:
        f.write(ocr_text)
    o = OcrInfo(
        filename=ocr_path.name,
        sha256=generate_sha256(ocr_path),
        lang=lang,
    )
    o.add_ocr_text(ocr_text)
    return o


def parse_html(
    src_html_dir: str,
    src_procedure_path: str,
    output_dir: str,
    image_params: list[ImageConvertParam] | None = None,
    ocr_target: List[OCR_TARGET] | None = None,
    image_max_workers: int | None = None,
) -> None:
    """Parse a JPO e-filing HTM directory and generate XML + WebP outputs."""

    src_dir = Path(src_html_dir)
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Source HTML directory not found: {src_html_dir}")
    if not Path(src_procedure_path).exists():
        raise FileNotFoundError(f"Source procedure XML not found: {src_procedure_path}")

    output_root = Path(output_dir)
    p = Paths.create(output_root)

    ### find and parse the HTM file
    htm_path = find_htm_file(src_dir)
    lines = read_htm(htm_path)
    doc = parse_html_text(lines)

    ### write appb.xml and jpbibl.xml to xml_dir
    xml_files: list[XmlFile] = []
    for filename, content in [
        ("JPOXMLDOC01-appb.xml", build_appb_xml(doc)),
        ("JPOXMLDOC01-jpbibl.xml", build_jpbibl_xml(doc)),
    ]:
        out_path = p.xml_dir / filename
        out_path.write_text(content, encoding="utf-8")
        xml_files.append(
            XmlFile(
                filename=filename,
                sha256=generate_sha256(out_path),
                encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
                kind=detect_xml_kind(filename),
            )
        )

    ### copy and rename GIF files to raw_dir as JPOXMLDOC01-appb-D000001.gif ...
    for fig in doc.figures:
        src_img = src_dir / fig.src
        dst_name = f"JPOXMLDOC01-appb-D{fig.num:06d}.gif"
        dst_img = p.raw_dir / dst_name
        if src_img.exists():
            shutil.copy2(src_img, dst_img)

    ### copy procedure.xml (already UTF-8 for HTML input)
    proc_xml_path = p.xml_dir / "procedure.xml"
    shutil.copy2(src_procedure_path, proc_xml_path)
    xml_files.append(
        XmlFile(
            filename=proc_xml_path.name,
            encoding=EncodingInfo(detected=None, normalized_to="UTF-8"),
            sha256=generate_sha256(proc_xml_path),
            kind=detect_xml_kind(proc_xml_path.name),
        )
    )

    ### guess language
    lang = guess_language_by_filename(str(p.xml_dir))

    params = image_params if image_params is not None else defaultImageParams

    ### process images (GIFs in raw_dir)
    gif_images = list(p.raw_dir.glob("*.gif", case_sensitive=False))
    images = process_images(
        gif_images,
        p.images_dir,
        p.ocr_dir,
        params,
        lang,
        ocr_target,
        max_workers=image_max_workers,
    )

    ### generate images-information.xml
    image_info_xml_path = p.xml_dir / "images-information.xml"
    ImageEntry.save_as_xml(images, image_info_xml_path)
    xml_files.append(XmlFile.to_xml_file(image_info_xml_path, kind="images-information"))

    ### generate sources.xml
    archive_source = Source.create(htm_path)
    procedure_source = Source.create(src_procedure_path)
    document_code = doc.file_reference_id or "UNKNOWN"
    sources = Sources(
        document_code=document_code,
        archive=archive_source,
        procedure=procedure_source,
    )
    sources_xml_path = p.xml_dir / "sources.xml"
    sources.save_as_xml(sources_xml_path)
    xml_files.append(XmlFile.to_xml_file(sources_xml_path, kind="source"))

    ### calc stats and generate manifest
    stats = Stats.create(p)
    manifest = Manifest.create(
        sources,
        xml_files,
        images,
        p.relative_to(p.root),
        stats,
    )
    manifest.save_as_json(p.root / "manifest.json")


def sanitize_text(text: str) -> str:
    """Sanitize text by removing control characters and trimming whitespace."""
    # remove quote, double quote, backslash, brackets, etc.
    # that may cause issues in downstream processing
    sanitized = re.sub(r"[!@#$%&*()\-_+=\[\]{}:;\"',./<>?^`|~\\]", "", text)
    sanitized = re.sub(
        r"\s+", " ", sanitized
    )  # replace multiple whitespace with single space
    sanitized = sanitized.replace("\r", "")  # remove carriage return
    sanitized = sanitized.replace("\n", "")  # remove newline
    return sanitized.strip()
