import hashlib
from pathlib import Path


def generate_sha256(file_path: str | Path) -> str:
    """return document sha256 based on file_path content

    Args:
        file_path (str | Path): file path

    Returns:
        str: document sha256
    """
    sha256_hash = hashlib.sha256()
    if isinstance(file_path, Path):
        file_path = str(file_path)
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
