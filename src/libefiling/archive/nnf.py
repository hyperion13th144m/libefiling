import struct
from .handler import ArchiveHandler


class ArchiveHandlerH16(ArchiveHandler):
    """
    this class handles the archive having a 0x16 byte long header, dispatched from the Japan Patent Office.
    """

    def __init__(self, raw_data: bytes):
        super().__init__(raw_data)

    def _get_header_size(self):
        return 0x16

    def _get_first_part_size(self):
        buffer = self._raw_data[0x0E: 0x0E + 4]
        return struct.unpack('>L', buffer)[0]

    def _get_first_part(self):
        start = self._get_header_size() + self._get_some_information_size()
        fp_size = self._get_first_part_size()
        return self._raw_data[start: start + fp_size]

    def _get_second_part(self):
        start = self._get_header_size() + self._get_some_information_size() + \
            self._get_first_part_size()
        sp_size = self._get_second_part_size()
        return self._raw_data[start: start + sp_size]

    def _get_some_information_size(self):
        buffer = self._raw_data[0x0A: 0x0A + 4]
        return struct.unpack('>L', buffer)[0]


class ArchiveHandlerNNFJPC(ArchiveHandlerH16):
    """this class handles the archive with a JPC file extension

    NNF represents an archive dispatched from the Japan Patent Office.
    """

    def __init__(self, raw_data: bytes):
        super().__init__(raw_data)

    def _get_first_part(self):
        start = self._get_header_size() + self._get_some_information_size()
        sp_size = self._get_second_part_size()
        return self._raw_data[start: start + sp_size]

    def get_contents(self):
        return self._unzip(self._get_first_part())


class ArchiveHandlerNNFJWS(ArchiveHandlerH16):
    """this class handles the archive with a JWS file extension"""

    def __init__(self, raw_data: bytes):
        super().__init__(raw_data)

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        data = self._extract_data_from_wad(self._get_second_part())
        sp_files = self._decode_mime(data)
        return fp_files + sp_files


class ArchiveHandlerNNFJWX(ArchiveHandlerH16):
    """this class handles the archive with a JWX file extension"""

    def __init__(self, raw_data: bytes):
        super().__init__(raw_data)

    def get_contents(self):
        fp_files = self._unzip(self._get_first_part())
        data = self._extract_data_from_wad(self._get_second_part())
        sp_files = self._unzip(data)
        return fp_files + sp_files
