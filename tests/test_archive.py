import argparse
import os

from libefiling.archive.extract import extract_archive

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Archive Extraction")
    parser.add_argument(
        "archive",
        type=str,
        help="src archive path",
        default=os.environ.get("EXTRACT_SRC"),
    )
    parser.add_argument(
        "output_dir", type=str, help="Output directory for extracted files", default=os.curdir
    )
    args = parser.parse_args()
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    items = extract_archive(args.archive)
    for name, content in items:
        output_path = os.path.join(output_dir, name)
        with open(output_path, "wb") as f:
            f.write(content)
