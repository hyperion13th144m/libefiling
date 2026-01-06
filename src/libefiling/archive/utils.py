import hashlib
from pathlib import Path

### Internet naminで送受信したファイル名に基づいて、各種データを取得する関数群
### https://www.pcinfo.jpo.go.jp/site/3_support/2_faq/pdf/09_09_file-name.pdf


def generate_sha256(archive_path: str) -> str:
    """return document sha256 based on archive_path content

    Args:
        archive_path (str): archive path

    Returns:
        str: document sha256
    """
    sha256_hash = hashlib.sha256()
    with open(archive_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_document_task(archive_path: str) -> str:
    """return document task based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: document task
    """
    if len(archive_path) != 63:
        return ""
    return Path(archive_path).stem[56 : 56 + 1]


def get_document_kind(archive_path: str) -> str:
    """return document kind based on archive_path name

    Args:
        archive_path (str): archive path

    Returns:
        str: document kind
    """
    if len(archive_path) != 63:
        return ""
    return Path(archive_path).stem[57 : 57 + 2]
