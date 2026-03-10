import re
from typing import Literal, TypedDict

XML_KIND = Literal[
    "pkgheader",
    "package-data",
    "image-list",
    "file-list",
    "management-info",
    "notice",
    "request",
    "declaration",
    "power-of-attorney",
    "fee-sheet",
    "indication-bio-deposit",
    "bibliographic-info",
    "application-body",
    "drawings",
    "foreign-language-body",
    "sequence-list",
    "st26-sequence-list",
    "attached-documents",
    "special-attached-documents",
    "special-st26-sequence-list",
    "procedure",
    "unknown",
]


class XML_RE_MAP(TypedDict):
    kind: XML_KIND
    regex: re.Pattern
    description: str


re_xml: list[XML_RE_MAP] = [
    {
        "kind": "pkgheader",
        "regex": re.compile(r"JPOXMLDOC01-pkgh\.xml"),
        "description": "pkgheader XML JPOXMLDOC01-pkgh.xml",
    },
    {
        "kind": "package-data",
        "regex": re.compile(r"JPOXMLDOC01-pkda\.xml"),
        "description": "package-data XML JPOXMLDOC01-pkda.xml",
    },
    {
        "kind": "image-list",
        "regex": re.compile(r"JPOXMLDOC01-jpflst\.xml"),
        "description": "イメージ一覧",
    },
    {
        "kind": "file-list",
        "regex": re.compile(r".+-jpflst\.xml"),
        "description": "ファイル一覧",
    },
    {
        "kind": "management-info",
        "regex": re.compile(r".+-jpmngt\.xml"),
        "description": "管理情報",
    },
    {
        "kind": "request",
        "regex": re.compile(r"JPOXMLDOC01-requ\.xml"),
        "description": "request XML",
    },
    {
        "kind": "declaration",
        "regex": re.compile(r"JPOXMLDOC\d{2}-decl\.xml"),
        "description": "declaration XML",
    },
    {
        "kind": "power-of-attorney",
        "regex": re.compile(r"JPOXMLDOC\d{2}-poat\.xml"),
        "description": "power-of-attorney XML",
    },
    {
        "kind": "fee-sheet",
        "regex": re.compile(r"JPOXMLDOC01-fees\.xml"),
        "description": "fee-sheet XML",
    },
    {
        "kind": "indication-bio-deposit",
        "regex": re.compile(r"JPOXMLDOC\d{2}-biod\.xml"),
        "description": "indication-bio-deposit XML",
    },
    {
        "kind": "bibliographic-info",
        "regex": re.compile(r"JPOXMLDOC01-jpbibl\.xml"),
        "description": "書誌情報 or 特殊申請 XML（送付票）",
    },
    {
        "kind": "application-body",
        "regex": re.compile(r"JPOXMLDOC01-appb\.xml"),
        "description": "application-body XML",
    },
    {
        "kind": "drawings",
        "regex": re.compile(r"JPOXMLDOC01-jpdrab\.xml"),
        "description": "図面の提出書",
    },
    {
        "kind": "foreign-language-body",
        "regex": re.compile(r"JPOXMLDOC01-jpfolb\.xml"),
        "description": "foreign-language-body XML",
    },
    {
        "kind": "sequence-list",
        "regex": re.compile(r"JPOXMLDOC01-jpseql\.xml"),
        "description": "配列表",
    },
    {
        "kind": "st26-sequence-list",
        "regex": re.compile(r"JPOXMLDOC01-seql\.xml"),
        "description": "ST.26 sequence-list XML",
    },
    {
        "kind": "attached-documents",
        "regex": re.compile(r"JPOXMLDOC01-jpatta\.xml"),
        "description": "添付書類（国内出願）",
    },
    {
        "kind": "special-attached-documents",
        "regex": re.compile(r"JPOXMLDOC01-jpsatt\.xml"),
        "description": "特殊申請 添付書類",
    },
    {
        "kind": "special-st26-sequence-list",
        "regex": re.compile(r"JPOXMLDOC01-seql-S\d{6}\.xml"),
        "description": "特殊申請 ST.26 sequence-list",
    },
    {
        "kind": "notice",
        "regex": re.compile(r".+-jpntce\.xml"),
        "description": "発送書類",
    },
    {
        "kind": "procedure",
        "regex": re.compile(r"procedure\.xml"),
        "description": "procedure XML procedure.xml",
    },
]


def detect_xml_kind(
    xml_name: str,
) -> XML_KIND:
    """detect XML kind from XML name

    Args:
        xml_name (str): XML name"""
    for re_map in re_xml:
        if re_map["regex"].match(xml_name):
            return re_map["kind"]
    return "unknown"
