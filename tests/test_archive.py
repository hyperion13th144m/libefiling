import argparse

from libefiling.archive.extract import extract_archive

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Archive Extraction")
    parser.add_argument(
        "archive",
        type=str,
        help="src archive path",
    )
    parser.add_argument(
        "output_dir", type=str, help="Output directory for extracted files"
    )
    args = parser.parse_args()
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)
    items = extract_archive(args.archive)
    for name, content in items:
        output_path = os.path.join(output_dir, name)
        with open(output_path, "wb") as f:
            f.write(content)
