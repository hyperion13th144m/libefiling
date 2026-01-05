import hashlib
import shutil
from datetime import datetime
from itertools import chain
from pathlib import Path

from libefiling.archive.utils import detect_document_id
from libefiling.image.mediatype import get_media_type
from libefiling.image.results import ImageConvertResult
from libefiling.manifest.model import (
    ArchiveSource,
    DerivedImage,
    DocumentInfo,
    EncodingInfo,
    GeneratorInfo,
    ImageEntry,
    Manifest,
    OcrInfo,
    OriginalImage,
    ProcedureSource,
    Stats,
    XmlFile,
)

from .archive.extract import extract_archive
from .charset.convert import convert_xml_charset
from .default_config import defaultImageParams
from .image.convert import convert_image
from .image.params import ImageConvertParam
from .ocr.ocr import guess_language_by_filename, ocr_image


def generate_sha256(file_path: str) -> str:
    """generate sha256 checksum of a file.

    Args:
        file_path (str): path to the file.

    Returns:
        str: sha256 checksum as a hex string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def parse_archive(
    src_archive_path: str,
    src_procedure_path: str,
    output_dir: str,
    image_params: list[ImageConvertParam] = defaultImageParams,
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
    raw_dir = output_root / "raw"
    xml_dir = output_root / "xml"
    images_dir = output_root / "images"
    ocr_dir = output_root / "ocr"
    for d in [raw_dir, xml_dir, images_dir, ocr_dir]:
        d.mkdir(parents=True, exist_ok=True)

    ### extract archive to raw_dir
    ### convert charset of extracted XML files to UTF-8 and save to xml_dir
    xml_files = []
    extracted_archives = extract_archive(src_archive_path)
    for filename, data in extracted_archives:

        ### save extracted file to raw_dir
        output_path = raw_dir / filename
        with open(output_path, "wb") as f:
            f.write(data)

        if not filename.lower().endswith(".xml"):
            continue

        ### convert charset of xml file and save to xml_dir
        convert_xml_charset(str(output_path), str(xml_dir / filename))

        ### record xml file info
        xml_path = xml_dir / filename
        xml_files.append(
            XmlFile(
                path=str(xml_path.relative_to(output_root)),
                original_path=str(output_path.relative_to(output_root)),
                sha256=generate_sha256(str(xml_path)),
                encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
            )
        )

    ### convert charset of procedure xml to UTF-8 and save to temp_xml_dir
    orig_xml_path = f"{raw_dir}/{Path(src_procedure_path).name}"
    shutil.copy(src_procedure_path, orig_xml_path)
    xml_path = Path(f"{xml_dir}/procedure.xml")
    convert_xml_charset(src_procedure_path, xml_path)
    xml_files.append(
        XmlFile(
            path=str(xml_path.relative_to(output_root)),
            original_path=str(Path(orig_xml_path).relative_to(output_root)),
            sha256=generate_sha256(str(xml_path)),
            encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
        )
    )

    ### guess language
    lang = guess_language_by_filename(xml_dir)

    ### convert images
    images = []
    ic_result = ImageConvertResult()
    src_images = chain(
        Path(raw_dir).glob("*.tif", case_sensitive=False),
        Path(raw_dir).glob("*.jpg", case_sensitive=False),
    )

    for image in src_images:
        ### convert image and save to images_dir
        results = convert_image(image, images_dir, image_params)
        ic_result.add_results(results.results)

        ### prepare DerivedImage entries
        derived_images = [
            DerivedImage(
                path=str(images_dir.relative_to(output_root) / result["new"]),
                sha256=generate_sha256(str(images_dir / result["new"])),
                width=int(result["width"]),
                height=int(result["height"]),
                size_tag=result.get("sizeTag", "unknown"),
                media_type=get_media_type(result["format"] or ""),
            )
            for result in results.results
        ]

        ### perform OCR on image and save results as JSON
        ocr_text = ocr_image(image, lang=lang)
        ocr_path = ocr_dir / (Path(image).stem + ".txt")
        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write(ocr_text)

        images.append(
            ImageEntry(
                id=Path(image).stem,
                original=OriginalImage(
                    path=str(raw_dir.relative_to(output_root) / image.name),
                    sha256=generate_sha256(str(raw_dir / image.name)),
                    media_type=get_media_type(image.suffix),
                ),
                derived=derived_images,
                ocr=OcrInfo(
                    path=str(ocr_path.relative_to(output_root)),
                    sha256=generate_sha256(str(ocr_path)),
                    lang=lang,
                ),
            )
        )

    ### save conversion results as XML
    xml_path = Path(f"{xml_dir}/image_conversion_results.xml")
    ic_result.save_as_xml(str(xml_path))
    xml_files.append(
        XmlFile(
            path=str(xml_path.relative_to(output_root)),
            original_path="",
            sha256=generate_sha256(str(xml_path)),
            encoding=EncodingInfo(detected="unknown", normalized_to="UTF-8"),
        )
    )

    manifest = Manifest(
        generator=GeneratorInfo(
            name="libefiling",
            version="0.1.0",
            created_at=datetime.now(),
        ),
        document=DocumentInfo(
            doc_id=detect_document_id(str(Path(src_archive_path))),
            source=ArchiveSource(
                archive_filename=Path(src_archive_path).name,
                archive_sha256=generate_sha256(str(src_archive_path)),
                byte_size=Path(src_archive_path).stat().st_size,
            ),
            procedure_source=ProcedureSource(
                procedure_filename=Path(src_procedure_path).name,
                procedure_sha256=generate_sha256(str(src_procedure_path)),
                byte_size=Path(src_procedure_path).stat().st_size,
            ),
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

    output_path = output_root / "manifest.json"
    output_path.write_text(
        manifest.model_dump_json(indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
