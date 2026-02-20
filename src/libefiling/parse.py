import shutil
from datetime import datetime
from importlib.metadata import version as get_version
from itertools import chain
from pathlib import Path
from typing import Iterator, List, Literal, Union, get_args

from libefiling.archive.utils import generate_sha256
from libefiling.image.kind import OCR_TARGET, detect_image_kind
from libefiling.image.mediatype import get_media_type
from libefiling.manifest import (
    DerivedImage,
    DocumentInfo,
    EncodingInfo,
    GeneratorInfo,
    ImageAttributes,
    ImageEntry,
    Manifest,
    OcrInfo,
    Source,
    Stats,
    XmlFile,
)

from .archive.extract import extract_archive
from .charset import convert_xml_charset
from .default_config import defaultImageParams
from .image.convert import convert_image
from .image.ocr import guess_language_by_filename, ocr_image
from .image.params import ImageConvertParam


def parse_archive(
    src_archive_path: str,
    src_procedure_path: str,
    output_dir: str,
    image_params: list[ImageConvertParam] = defaultImageParams,
    ocr_target: List[OCR_TARGET] | None = None,
):
    """parse e-filing archive and generate various outputs."""

    if not Path(src_archive_path).exists():
        raise FileNotFoundError(f"Source archive not found: {src_archive_path}")
    if not Path(src_procedure_path).exists():
        raise FileNotFoundError(f"Source procedure XML not found: {src_procedure_path}")
    output_root = Path(output_dir)
    if not output_root.exists():
        output_root.mkdir(parents=True, exist_ok=True)

    extracted_files = extract_archive(src_archive_path)

    ### create output subdirectories
    raw_dir = output_root / "raw"
    xml_dir = output_root / "xml"
    images_dir = output_root / "images"
    ocr_dir = output_root / "ocr"
    for d in [raw_dir, xml_dir, images_dir, ocr_dir]:
        d.mkdir(parents=True, exist_ok=True)

    ### extract archive to raw_dir
    save_raw_files(extracted_files, raw_dir)

    ### convert charset of extracted XML files to UTF-8 and save to xml_dir
    raw_xml_files = raw_dir.glob("*.xml", case_sensitive=False)
    xml_files = process_xml(raw_xml_files, xml_dir)

    ### convert charset of procedure xml to UTF-8 and save to xml_dir
    xml_files.append(process_procedure_xml(Path(src_procedure_path), xml_dir))

    ### guess language
    lang = guess_language_by_filename(str(xml_dir))

    ### process images
    src_images = chain(
        Path(raw_dir).glob("*.tif", case_sensitive=False),
        Path(raw_dir).glob("*.jpg", case_sensitive=False),
    )
    images = process_images(
        src_images, images_dir, ocr_dir, image_params, lang, ocr_target
    )

    # generate manifest
    manifest = process_manifest(
        src_archive_path,
        src_procedure_path,
        str(xml_dir),
        xml_files,
        images,
    )

    manifest_path = output_root / "manifest.json"
    manifest_path.write_text(
        manifest.model_dump_json(indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


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
            )
        )

    return xml_files


def process_procedure_xml(
    src_procedure_path: Path,
    xml_dir: Path,
    filename: str = "procedure.xml",
) -> XmlFile:
    xml_path = xml_dir / filename
    convert_xml_charset(str(src_procedure_path), str(xml_path))
    return XmlFile(
        filename=filename,
        encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
        sha256=generate_sha256(xml_path),
    )


def process_images(
    image_files: chain[Path],
    images_dir: Path,
    ocr_dir: Path,
    image_params: list[ImageConvertParam],
    lang: str,
    ocr_target: List[OCR_TARGET] | None = None,
) -> list[ImageEntry]:
    images = []

    for image in image_files:
        derived_images = convert_images(image, images_dir, image_params)

        if ocr_target is not None:
            image_kind = detect_image_kind(image.name)
            if image_kind in ocr_target or "ALL" in ocr_target:
                ocr = get_ocr_text(image, ocr_dir, lang)
            else:
                ocr = None
        else:
            ocr = None
        images.append(
            ImageEntry(
                filename=image.name,
                sha256=generate_sha256(image),
                media_type=get_media_type(image.suffix),
                kind=detect_image_kind(image.name),
                derived=derived_images,
                ocr=ocr,
            )
        )
    return images


def convert_images(
    image: Path, images_dir: Path, image_params: list[ImageConvertParam]
) -> list[DerivedImage]:
    derived_images = []
    for param in image_params:
        suffix = param.suffix if param.suffix is not None else ""
        format = param.format if param.format is not None else ".webp"
        new = Path(image).stem + suffix + format
        derived_image_path = images_dir / new

        ### convert image and save to images_dir
        new_width, new_height = convert_image(
            image, derived_image_path, param.width, param.height
        )

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


def get_ocr_text(image: Path, ocr_dir: Path, lang: str) -> OcrInfo:
    ocr_text = ocr_image(str(image), lang=lang)
    ocr_path = ocr_dir / (Path(image).stem + ".txt")
    with open(ocr_path, "w", encoding="utf-8") as f:
        f.write(ocr_text)
    return OcrInfo(
        filename=ocr_path.name,
        sha256=generate_sha256(ocr_path),
        lang=lang,
    )


def process_manifest(
    src_archive_path: str,
    src_procedure_path: str,
    xml_dir: str,
    xml_files: list[XmlFile],
    images: list[ImageEntry],
) -> Manifest:
    manifest = Manifest(
        generator=GeneratorInfo(
            name="libefiling",
            version=get_version("libefiling"),
            created_at=datetime.now(),
        ),
        document=DocumentInfo(
            doc_id=generate_sha256(src_archive_path),
            sources=[
                Source.create(
                    src_archive_path, sha256=generate_sha256(src_archive_path)
                ),
                Source.create(
                    src_procedure_path, sha256=generate_sha256(src_procedure_path)
                ),
            ],
        ),
        xml_files=xml_files,
        images=images,
        stats=Stats(
            xml_count=len(list(Path(xml_dir).glob("*.xml"))),
            image_original_count=len(images),
            image_derived_count=sum(len(img.derived) for img in images),
            ocr_result_count=len(images),
        ),
    )

    return manifest
