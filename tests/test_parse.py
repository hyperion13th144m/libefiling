import argparse
import os
import sys

from dotenv import load_dotenv

from libefiling import parse_archive

if __name__ == "__main__":
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
    args = parser.parse_args()
    # load_dotenv()
    # EXTRACT_SRC = os.environ.get("EXTRACT_SRC")
    # PROCEDURE_SRC = os.environ.get("PROCEDURE_SRC")
    parse_archive(
        args.archive, args.procedure, args.out_dir, ocr_target=["other-images"]
    )
