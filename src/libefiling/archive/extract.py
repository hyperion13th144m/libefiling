from typing import List, Tuple

from .aaa import (
    ArchiveHandlerAAAJPC,
    ArchiveHandlerAAAJPD,
    ArchiveHandlerAAAJWS,
    ArchiveHandlerAAAJWX,
)
from .handler import ArchiveHandler
from .nnf import ArchiveHandlerNNFJPC, ArchiveHandlerNNFJWS, ArchiveHandlerNNFJWX

handlers: List[type[ArchiveHandler]] = [
    ArchiveHandlerAAAJPC,
    ArchiveHandlerAAAJPD,
    ArchiveHandlerAAAJWS,
    ArchiveHandlerAAAJWX,
    ArchiveHandlerNNFJPC,
    ArchiveHandlerNNFJWS,
    ArchiveHandlerNNFJWX,
]


def extract_archive(archive_path: str) -> List[Tuple[str, bytes]]:
    """extract all files from the archive.

    Args:
        archive_path (str): Path of the archive
    Returns:
        List[Tuple[str, bytes]]: List of extracted files as (filename, data) tuples
    Raises:
        ValueError: when the archive format is unsupported
    """
    with open(archive_path, "rb") as stream:
        raw_data = stream.read()

    for handler_cls in handlers:
        handler = handler_cls(raw_data)
        if handler.is_valid():
            return handler.get_contents()
    else:
        raise ValueError(f"unsupported archive format: {archive_path.name}")
