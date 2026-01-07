import sys
from pathlib import Path

from libefiling.charset import convert_xml_charset

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_archive.py <src_dir> <dst_dir>")
        sys.exit(1)

    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    for src in Path(src_dir).glob("*.xml", case_sensitive=False):
        dst_path = Path(dst_dir) / src.name
        convert_xml_charset(src, dst_path)
