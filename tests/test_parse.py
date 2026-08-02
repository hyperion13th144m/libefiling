import argparse

from libefiling import parse_archive

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Archive Parsing")
    parser.add_argument(
        "archive",
        type=str,
        help="src archive path",
    )
    parser.add_argument(
        "procedure",
        type=str,
        help="procedure file path",
    )
    parser.add_argument(
        "out_dir",
        type=str,
        help="Output directory for parsed files",
    )
    args = parser.parse_args()
    parse_archive(args.archive, args.procedure, args.out_dir)
