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
    image = Image.open(src_image_path)
    text = pytesseract.image_to_string(image, lang)
    return text


def guess_language_by_filename(src_xml_dir: str) -> str:
    """guess language from xml filename in src_xml_dir

    Args:
        src_xml_dir (str): path to directory containing xml files.
    """
    files = Path(src_xml_dir).glob("JPOXMLDOC01-jpfolb*.xml", case_sensitive=False)
    if len(list(files)) > 0:
        return "eng"
    else:
        return "jpn"
