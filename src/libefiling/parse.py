import shutil
from datetime import datetime
from importlib.metadata import version as get_version
from itertools import chain
from pathlib import Path

from libefiling.archive.utils import (
    generate_sha256,
    get_document_kind,
    get_document_task,
)
from libefiling.image.kind import detect_image_kind
from libefiling.image.mediatype import get_media_type
from libefiling.image.save_as_xml import save_as_xml
from libefiling.manifest import (
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
):
    """parse e-filing archive and generate various outputs."""

    if not Path(src_archive_path).exists():
        raise FileNotFoundError(f"Source archive not found: {src_archive_path}")
    if not Path(src_procedure_path).exists():
        raise FileNotFoundError(f"Source procedure XML not found: {src_procedure_path}")
    output_root = Path(output_dir)
    if not output_root.exists():
        output_root.mkdir(parents=True, exist_ok=True)

    extracted_archives = extract_archive(src_archive_path)

    ### create output subdirectories
    raw_dir = output_root / "raw"
    xml_dir = output_root / "xml"
    images_dir = output_root / "images"
    ocr_dir = output_root / "ocr"
    for d in [raw_dir, xml_dir, images_dir, ocr_dir]:
        d.mkdir(parents=True, exist_ok=True)

    ### extract archive to raw_dir
    ### convert charset of extracted XML files to UTF-8 and save to xml_dir
    xml_files = process_archive(extracted_archives, output_root, raw_dir, xml_dir)

    ### convert charset of procedure xml to UTF-8 and save to xml_dir
    xml_files.append(
        process_procedure_xml(src_procedure_path, output_root, raw_dir, xml_dir)
    )

    ### guess language
    lang = guess_language_by_filename(xml_dir)

    ### convert images
    images = process_images(
        raw_dir, images_dir, ocr_dir, output_root, image_params, lang
    )

    ### save conversion results as XML
    xml_files.append(
        process_conversion_results(xml_dir, images, output_root, xml_files)
    )

    manifest = process_manifest(
        src_archive_path,
        src_procedure_path,
        xml_dir,
        xml_files,
        images,
    )

    output_path = output_root / "manifest.json"
    output_path.write_text(
        manifest.model_dump_json(indent=4, ensure_ascii=False),
        encoding="utf-8",
    )


def process_archive(
    extracted_archives: list[tuple[str, bytes]],
    output_root: Path,
    raw_dir: Path,
    xml_dir: Path,
) -> list[XmlFile]:
    xml_files = []
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

    return xml_files


def process_procedure_xml(
    src_procedure_path: Path,
    output_root: Path,
    raw_dir: Path,
    xml_dir: Path,
) -> XmlFile:
    ### copy original procedure xml to raw_dir
    orig_xml_path = f"{raw_dir}/{Path(src_procedure_path).name}"
    shutil.copy(src_procedure_path, orig_xml_path)

    ### convert charset of procedure xml to UTF-8 and save to temp_xml_dir
    xml_path = Path(f"{xml_dir}/procedure.xml")
    convert_xml_charset(src_procedure_path, xml_path)
    return XmlFile(
        path=str(xml_path.relative_to(output_root)),
        original_path=str(Path(orig_xml_path).relative_to(output_root)),
        sha256=generate_sha256(str(xml_path)),
        encoding=EncodingInfo(detected="shift_jis", normalized_to="UTF-8"),
    )


def process_images(
    raw_dir: Path,
    images_dir: Path,
    ocr_dir: Path,
    output_root: Path,
    image_params: list[ImageConvertParam],
    lang: str,
) -> list[ImageEntry]:
    images = []
    src_images = chain(
        Path(raw_dir).glob("*.tif", case_sensitive=False),
        Path(raw_dir).glob("*.jpg", case_sensitive=False),
    )

    for image in src_images:
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
            attributes = [attr.model_dump() for attr in param.attributes]
            derived_images.append(
                DerivedImage(
                    path=str(images_dir.relative_to(output_root) / new),
                    sha256=generate_sha256(derived_image_path),
                    width=new_width,
                    height=new_height,
                    attributes=attributes,
                    media_type=get_media_type(Path(new).suffix or ""),
                )
            )

        ### perform OCR on image and save results as text
        ocr_text = ocr_image(image, lang=lang)
        ocr_path = ocr_dir / (Path(image).stem + ".txt")
        with open(ocr_path, "w", encoding="utf-8") as f:
            f.write(ocr_text)

        images.append(
            ImageEntry(
                id=Path(image).stem,
                kind=detect_image_kind(image.name),
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
    return images


def process_conversion_results(
    xml_dir: Path, images: list[ImageEntry], output_root: Path, xml_files: list[XmlFile]
):
    ### save conversion results as XML
    xml_path = Path(f"{xml_dir}/image_conversion_results.xml")
    save_as_xml(images, str(xml_path))
    return XmlFile(
        path=str(xml_path.relative_to(output_root)),
        original_path="",
        sha256=generate_sha256(str(xml_path)),
        encoding=EncodingInfo(detected="unknown", normalized_to="UTF-8"),
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
            source=ArchiveSource(
                archive_filename=Path(src_archive_path).name,
                archive_sha256=generate_sha256(src_archive_path),
                byte_size=Path(src_archive_path).stat().st_size,
                task=get_document_task(Path(src_archive_path).name),
                kind=get_document_kind(Path(src_archive_path).name),
                extension=Path(src_archive_path).suffix.upper(),
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

    return manifest
