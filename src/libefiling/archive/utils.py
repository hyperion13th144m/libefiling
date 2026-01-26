import hashlib
from pathlib import Path


def generate_sha256(archive_path: str | Path) -> str:
    """return document sha256 based on archive_path content

    Args:
        archive_path (str | Path): archive path

    Returns:
        str: document sha256
    """
    sha256_hash = hashlib.sha256()
    if isinstance(archive_path, Path):
        archive_path = str(archive_path)
    with open(archive_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()
