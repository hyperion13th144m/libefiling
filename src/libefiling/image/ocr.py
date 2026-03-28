from pathlib import Path

import pytesseract
from PIL import Image


def ocr_image(src_image_path: str, lang: str) -> str:
    """extract text from images

    Args:
        src_image_path (str): _description_
        lang (str): eng, jpn

    Returns:
        str: text extracted from image
    """
    with Image.open(src_image_path) as image:
        return pytesseract.image_to_string(image, lang)


def guess_language_by_filename(src_xml_dir: str) -> str:
    """guess language from xml filename in src_xml_dir

    Args:
        src_xml_dir (str): path to directory containing xml files.
    """
    files = Path(src_xml_dir).glob("JPOXMLDOC01-jpfolb*.xml", case_sensitive=False)
    if any(files):
        return "eng"
    else:
        return "jpn"
