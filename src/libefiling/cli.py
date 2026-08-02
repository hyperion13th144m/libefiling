import argparse
from importlib.metadata import version

from libefiling import parse_archive


def main():
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
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('libefiling')}"
    )
    args = parser.parse_args()

    parse_archive(
        args.archive,
        args.procedure,
        args.out_dir,
    )
