from pathlib import Path
from typing import List, Tuple

from ..utils.archive import detect_document_extension, detect_document_kind
from .aaa import (
    ArchiveHandlerAAAJPC,
    ArchiveHandlerAAAJPD,
    ArchiveHandlerAAAJWS,
    ArchiveHandlerAAAJWX,
)
from .check import check_archive_name
from .handler import ArchiveHandler
from .nnf import ArchiveHandlerNNFJPC, ArchiveHandlerNNFJWS, ArchiveHandlerNNFJWX


def extract_archive(archive_path: str) -> List[Tuple[str, bytes]]:
    """extract all files from the archive.

    Args:
        archive_path (str): Path of the archive
    """
    archive_path = Path(archive_path)
    if check_archive_name(archive_path) is False:
        raise ValueError(f"archive name {archive_path.name} is invalid")

    handler = create_handler(archive_path)
    return handler.get_contents()


def create_handler(archive_path: Path) -> "ArchiveHandler":
    """factory method to create an instance of ArchiveHandler

    Args:
        archive_path (Path): Path of the archive

    Returns:
        ArchiveHandler: an instance of ArchiveHandler
    """
    ext = detect_document_extension(str(archive_path))
    kind = detect_document_kind(str(archive_path))

    if kind == "AAA" or kind == "AER":
        if ext == ".JWX":
            handler = ArchiveHandlerAAAJWX
        elif ext == ".JWS":
            handler = ArchiveHandlerAAAJWS
        elif ext == ".JPC":
            handler = ArchiveHandlerAAAJPC
        elif ext == ".JPD":
            handler = ArchiveHandlerAAAJPD
        else:
            raise ValueError(f"unknwon file format: {archive_path}")
        # extension 'JPB' is not supported due to the lack of actual data
        # if ext == ArchiveExt.JPB:
        #     return unkown
    elif kind == "NNF":
        if ext == ".JWX":
            handler = ArchiveHandlerNNFJWX
        elif ext == ".JWS":
            handler = ArchiveHandlerNNFJWS
        elif ext == ".JPC":
            handler = ArchiveHandlerNNFJPC
        else:
            raise ValueError(f"unknwon file format: {archive_path}")
        # extension JPD and JPB is not supported due to the lack of actual data
        # elif self.kind == ArchiveKind.NNF:
        #     if ext == ArchiveExt.JPD:
        #         return unknown
        #     if ext == ArchiveExt.JPB:
        #         return unknown
    else:
        raise ValueError(f"unknwon file format: {archive_path}")

    with archive_path.open("rb") as stream:
        archive_handler = handler(stream.read())
    return archive_handler
