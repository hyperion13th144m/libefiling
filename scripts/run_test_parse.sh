#!/bin/bash

T=${1:-1}

# T is defined in .envrc.
export T
direnv reload
uv run python tests/test_parse.py $SRC1 $SRC2 $OUTPUT_DIR
