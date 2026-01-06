import struct

from .handler import ArchiveHandler


class ArchiveHandlerH32(ArchiveHandler):
    """
    this class handles the archive having a 0x32 byte long header,
    submitted to the Japan Patent Office.
    """

    def _get_header_size(self):
        return 0x32

    def _get_first_part_size(self):
        buffer = self._raw_data[0x0A : 0x0A + 4]
        return struct.unpack(">L", buffer)[0]

    def _get_first_part(self):
        start = self._get_header_size()
        fp_size = self._get_first_part_size()
        return self._raw_data[start : start + fp_size]

    def _get_second_part(self):
        start = self._get_header_size() + self._get_first_part_size()
        sp_size = self._get_second_part_size()
        return self._raw_data[start : start + sp_size]

    def _get_some_information_size(self):
        return 0


class ArchiveHandlerAAAJPC(ArchiveHandlerH32):
    """this class handles the archive,
    task: A
    kind: AA
    extension: JPC
    """

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        sp_files = self._unzip(self._get_second_part())
        return fp_files + sp_files

    def is_valid(self) -> bool:
        # magic number: 30-31-32-30-31-30
        signature = self._get_signature()
        return signature == b"\x30\x31\x32\x30\x31\x30"


class ArchiveHandlerAAAJWX(ArchiveHandlerH32):
    """this class handles the archive,
    task: A
    kind: AA
    extension: JWX
    """

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        data = self._extract_data_from_wad(self._get_second_part())
        sp_files = self._unzip(data)
        return fp_files + sp_files

    def is_valid(self) -> bool:
        # magic number: 49-31-32-30-31-30
        signature = self._get_signature()
        return signature == b"\x49\x31\x32\x30\x31\x30"


class ArchiveHandlerAAAJPD(ArchiveHandlerH32):
    """this class handles the archive,
    task: A
    kind: AA
    extension: JPD
    """

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        sp_files = self._decode_mime(self._get_second_part())
        return fp_files + sp_files

    def is_valid(self) -> bool:
        # magic number: 30-31-33-30-31-30
        signature = self._get_signature()
        return signature == b"\x30\x31\x33\x30\x31\x30"


class ArchiveHandlerAAAJWS(ArchiveHandlerH32):
    """this class handles the archive,
    task: A
    kind: AA
    extension: JWS
    """

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        data = self._extract_data_from_wad(self._get_second_part())
        sp_files = self._decode_mime(data)
        return fp_files + sp_files

    def is_valid(self) -> bool:
        # magic number: 49-31-33-30-31-30
        signature = self._get_signature()
        return signature == b"\x49\x31\x33\x30\x31\x30"
