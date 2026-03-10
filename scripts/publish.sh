#!/bin/sh

uv version --bump patch
uv build
uv publish


