import glob
import os
import sys
from pathlib import Path

from libefiling.ocr.ocr import guess_language_by_filename, ocr_image

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_image.py <src_dir> <dst_path>")
        sys.exit(1)

    src_dir = sys.argv[1]
    dst_path = sys.argv[2]
    if os.path.exists(src_dir):
        lang = guess_language_by_filename(src_dir)
    else:
        lang = "eng"
    src_images = list(Path(src_dir).glob("*.tif", case_sensitive=False)) + list(
        Path(src_dir).glob("*.jpg", case_sensitive=False)
    )
    for src_image in src_images:
        ocr_result = ocr_image(src_image, lang=lang)
        dst_path = Path(dst_path) / (src_image.stem + ".json")
        dst_path.write_text(ocr_result)
