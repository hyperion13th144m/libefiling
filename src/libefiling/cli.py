import argparse
import os
from importlib.metadata import version

from libefiling import parse_archive


def main():
    parser = argparse.ArgumentParser(description="Test Archive Parsing")
    parser.add_argument(
        "archive",
        nargs="?",
        type=str,
        help="src archive path (or EXTRACT_SRC env var)",
        default=os.environ.get("EXTRACT_SRC"),
    )
    parser.add_argument(
        "procedure",
        nargs="?",
        type=str,
        help="procedure file path (or PROCEDURE_SRC env var)",
        default=os.environ.get("PROCEDURE_SRC"),
    )
    parser.add_argument(
        "out_dir",
        nargs="?",
        type=str,
        help="Output directory for parsed files",
        default=os.environ.get("LIBEFILING_OUTPUT_DIR", os.curdir),
    )
    parser.add_argument(
        "--ocr-target",
        nargs="+",
        choices=[
            "chemical-formulas",
            "figures",
            "equations",
            "tables",
            "other-images",
            "ALL",
        ],
        help="Specify OCR target image kinds (default: None, which means no OCR)",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('libefiling')}"
    )
    args = parser.parse_args()

    if not args.archive:
        parser.error("archive is required (positional or EXTRACT_SRC env var)")
    if not args.procedure:
        parser.error("procedure is required (positional or PROCEDURE_SRC env var)")

    parse_archive(
        args.archive,
        args.procedure,
        args.out_dir,
        ocr_target=args.ocr_target,
    )
