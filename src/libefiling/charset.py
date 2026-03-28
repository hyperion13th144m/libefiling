import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("jp", "http://www.jpo.go.jp")


def convert_xml_charset(
    src_xml_path: str,
    dst_xml_path: str,
    from_encoding: str = "shift_jis",
    to_encoding: str = "utf-8",
):
    """convert charset of a set of xml files and replace header.

    Args:
        src_xml_path (str): path to file to be converted.
        dst_xml_path (str): path to file to be stored.
    """
    ### インターネット出願ソフト用XMLはShift_JISでエンコードされている。
    ### これをUTF-8に変換する。
    src_path = Path(src_xml_path)
    dst_path = Path(dst_xml_path)
    try:
        xml_text = src_path.read_text(encoding=from_encoding)
        root = ET.fromstring(xml_text)
        tree = ET.ElementTree(root)
        tree.write(dst_path, encoding=to_encoding, xml_declaration=True)
    except UnicodeDecodeError as exc:
        raise ValueError(
            f"Failed to decode XML with encoding '{from_encoding}': {src_path}"
        ) from exc
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML format: {src_path}") from exc
