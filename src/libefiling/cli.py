import argparse
import os
from importlib.metadata import version

from libefiling import parse_archive


def main():
    parser = argparse.ArgumentParser(description="Test Archive Parsing")
    parser.add_argument(
        "archive",
        type=str,
        help="src archive path",
        default=os.environ.get("EXTRACT_SRC"),
    )
    parser.add_argument(
        "procedure",
        type=str,
        help="procedure file path",
        default=os.environ.get("PROCEDURE_SRC"),
    )
    parser.add_argument(
        "out_dir", type=str, help="Output directory for parsed files", default=os.curdir
    )
    parser.add_argument(
        "--ocr-target",
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
    parse_archive(
        args.archive, args.procedure, args.out_dir, ocr_target=args.ocr_target
    )
