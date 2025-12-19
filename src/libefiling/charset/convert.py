import xml.etree.ElementTree as ET

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
    with open(src_xml_path, "r", encoding=from_encoding) as f:
        xml = ET.fromstring(f.read())
        et = ET.ElementTree(xml)
        et.write(dst_xml_path, to_encoding, True)
