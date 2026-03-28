import re
from typing import Literal

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
    "source",
    "images-information",
    "unknown",
]
_XML_KIND_RULES: tuple[tuple[XML_KIND, re.Pattern[str]], ...] = (
    ("pkgheader", re.compile(r"JPOXMLDOC01-pkgh\.xml")),
    ("package-data", re.compile(r"JPOXMLDOC01-pkda\.xml")),
    ("image-list", re.compile(r"JPOXMLDOC01-jpflst\.xml")),
    ("file-list", re.compile(r".+-jpflst\.xml")),
    ("management-info", re.compile(r".+-jpmngt\.xml")),
    ("request", re.compile(r"JPOXMLDOC01-requ\.xml")),
    ("declaration", re.compile(r"JPOXMLDOC\d{2}-decl\.xml")),
    ("power-of-attorney", re.compile(r"JPOXMLDOC\d{2}-poat\.xml")),
    ("fee-sheet", re.compile(r"JPOXMLDOC01-fees\.xml")),
    ("indication-bio-deposit", re.compile(r"JPOXMLDOC\d{2}-biod\.xml")),
    ("bibliographic-info", re.compile(r"JPOXMLDOC01-jpbibl\.xml")),
    ("application-body", re.compile(r"JPOXMLDOC01-appb\.xml")),
    ("drawings", re.compile(r"JPOXMLDOC01-jpdrab\.xml")),
    ("foreign-language-body", re.compile(r"JPOXMLDOC01-jpfolb\.xml")),
    ("sequence-list", re.compile(r"JPOXMLDOC01-jpseql\.xml")),
    ("st26-sequence-list", re.compile(r"JPOXMLDOC01-seql\.xml")),
    ("attached-documents", re.compile(r"JPOXMLDOC01-jpatta\.xml")),
    ("special-attached-documents", re.compile(r"JPOXMLDOC01-jpsatt\.xml")),
    (
        "special-st26-sequence-list",
        re.compile(r"JPOXMLDOC01-seql-S\d{6}\.xml"),
    ),
    ("notice", re.compile(r".+-jpntce\.xml")),
    ("procedure", re.compile(r"procedure\.xml")),
    ("source", re.compile(r"source\.xml")),
)


def detect_xml_kind(
    xml_name: str,
) -> XML_KIND:
    """detect XML kind from XML name

    Args:
        xml_name (str): XML name"""
    for kind, pattern in _XML_KIND_RULES:
        if pattern.fullmatch(xml_name):
            return kind
    return "unknown"
