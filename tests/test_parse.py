import os
import sys

from dotenv import load_dotenv

from libefiling import parse_archive

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_parse.py <out_dir>")
        sys.exit(1)

    load_dotenv()
    EXTRACT_SRC = os.environ.get("EXTRACT_SRC")
    PROCEDURE_SRC = os.environ.get("PROCEDURE_SRC")
    parse_archive(EXTRACT_SRC, PROCEDURE_SRC, sys.argv[1])
