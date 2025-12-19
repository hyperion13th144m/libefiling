import os
import sys

from dotenv import load_dotenv

from libefiling.archive.extract import extract_archive

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_archive.py <output_dir>")
        sys.exit(1)

    load_dotenv()
    EXTRACT_SRC = os.environ.get("EXTRACT_SRC")
    if not EXTRACT_SRC:
        print("Environment variable EXTRACT_SRC is not set.")
        sys.exit(1)
    output_dir = sys.argv[1]
    items = extract_archive(EXTRACT_SRC, output_dir)
    for name, content in items:
        output_path = os.path.join(output_dir, name)
        with open(output_path, "wb") as f:
            f.write(content)
