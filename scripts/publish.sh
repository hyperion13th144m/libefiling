#!/bin/sh

uv version --bump patch
version=$(uv version --short)
git tag -a v$version -m "Release version $version"

# Push the tag to the remote repository
# git push origin --tags


