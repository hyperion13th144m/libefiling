#!/bin/sh

poetry version patch
poetry build
poetry publish --repository pypi


