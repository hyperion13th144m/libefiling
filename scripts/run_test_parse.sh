#!/bin/bash

T=${1:-1}

# T is defined in .envrc.
export T
source .envrc

echo "Running test_parse.py with T=$T"
echo "SRC1: $SRC1"
echo "SRC2: $SRC2"
echo "OUTPUT_DIR: $OUTPUT_DIR"
uv run libefiling $SRC1 $SRC2 $OUTPUT_DIR
