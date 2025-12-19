import json
from pathlib import Path

import pytesseract
from PIL import Image


class OcrResult:
    def __init__(self):
        self.results = []

    def add_result(self, image_name: str, text: str):
        self.results.append({"image_name": image_name, "text": text})

    def save_as_json(self, file_path: str):
        results = sorted(self.results, key=lambda x: x["image_name"])
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump({"root": {"ocrText": results}}, f, ensure_ascii=False, indent=4)


def ocr_image(src_image_path: str, lang: str) -> str:
    """extract text from images

    Args:
        src_image_path (str): _description_
        lang (str): eng, jpn

    Returns:
        OcrResult: _description_
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
