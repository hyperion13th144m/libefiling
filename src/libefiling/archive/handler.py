import io
import struct
from abc import ABC, abstractmethod
from email import message_from_bytes
from typing import List, Tuple
from zipfile import ZipFile

from asn1crypto.cms import SignedData


class ArchiveHandler(ABC):
    """A base class for extracting files contained in archives
    with extensions JWX, JWC, JPC, and JPD used in internet application software.
    """

    def __init__(self, raw_data: bytes):
        self._raw_data = raw_data

    @abstractmethod
    def get_contents(self) -> List[Tuple[str, bytes]]:
        pass

    @abstractmethod
    def is_valid(self) -> bool:
        pass

    @abstractmethod
    def _get_header_size(self) -> int:
        """return the header size of the archive

        Returns:
            int: header size
        """
        pass

    def _get_signature(self) -> bytes:
        """return the signature of the archive

        6 bytes of the archive from 0x00 to 0x05 might be a signature representing the type of the rchive.

        Returns:
            bytes: the signature of the archive
        """
        return self._raw_data[0:6]

    def _get_payload_size(self) -> int:
        """return the size of the entire arhicve excluding the six-byte signature.

        Returns:
            int: payload size
        """
        buffer = self._raw_data[0x06 : 0x06 + 4]
        return struct.unpack(">L", buffer)[0]

    @abstractmethod
    def _get_first_part_size(self) -> int:
        """return the size of the first part of the payload

        Returns:
            int: the size of the first part
        """
        pass

    @abstractmethod
    def _get_first_part(self) -> bytes:
        """return the first part of the payload

        Returns:
            bytes: the first part
        """
        pass

    def _get_second_part_size(self) -> int:
        """return the size of the second part of the payload

        Returns:
            int: the size of the second part
        """
        buffer = self._raw_data[0x12 : 0x12 + 4]
        return struct.unpack(">L", buffer)[0]

    @abstractmethod
    def _get_second_part(self) -> bytes:
        """return the second part of the payload

        Returns:
            bytes: the second part
        """
        pass

    @abstractmethod
    def _get_some_information_size(self) -> int:
        """return the size of some information after the header.

        Returns:
            int: the size of some information size
        """
        pass

    def _unzip(self, data: bytes) -> List[Tuple[str, bytes]]:
        zip_stream = io.BytesIO(data)
        with ZipFile(zip_stream, "r") as zip_file:
            result = [(name, zip_file.read(name)) for name in zip_file.namelist()]
        return result

    def _extract_data_from_wad(self, data: bytes) -> bytes:
        """extract data part from WAD data.

        the data part is identified by oid; 1.2.840.113549.1.7.1
        WAD data is Wrapped Application Documents in ASN.1 format.
        see P7 of https://www.jpo.go.jp/system/patent/gaiyo/sesaku/document/touroku_jyohou_kikan/shomen-entry-02jpo-shiyosho.pdf
        """
        info = SignedData.load(data)  # type: ignore
        content = info["encap_content_info"]["content"]  # type: ignore
        return content.native  # type: ignore

    def _decode_mime(self, data: bytes) -> List[Tuple[str, bytes]]:
        """extract data part from MIME data."""
        mime = message_from_bytes(data)
        return [
            (filename, m.get_payload(decode=True))  # type: ignore
            for m in mime.walk()
            if (filename := m.get_filename()) is not None
        ]
