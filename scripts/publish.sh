#!/bin/sh

poetry version patch
poetry build -f wheel
poetry publish --repository pypi


