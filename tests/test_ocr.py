import glob
import os
import sys
from pathlib import Path

from libefiling.image.ocr import guess_language_by_filename, ocr_image

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python test_ocr.py <src_path> <dst_path> <lang>")
        sys.exit(1)

    src_path = sys.argv[1]
    dst_path = sys.argv[2]
    lang = sys.argv[3]
    ocr_text = ocr_image(src_path, lang=lang)
    Path(dst_path).write_text(ocr_text, encoding="utf-8")
