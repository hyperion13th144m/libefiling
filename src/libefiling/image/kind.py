import re
from typing import Literal

IMAGE_KIND = Literal[
    "chemical-formulas", "figures", "equations", "tables", "other-images", "unknown"
]
OCR_TARGET = Literal[
    "chemical-formulas", "figures", "equations", "tables", "other-images", "ALL"
]

_OPTIONAL_EXTENSION = r"(?:\.[A-Za-z0-9]+)?"
_KIND_RULES: tuple[tuple[IMAGE_KIND, re.Pattern[str]], ...] = (
    ("chemical-formulas", re.compile(rf".+-appb-C[0-9]+{_OPTIONAL_EXTENSION}")),
    ("figures", re.compile(rf".+-(appb|jpdrab)-D[0-9]+{_OPTIONAL_EXTENSION}")),
    ("equations", re.compile(rf".+-appb-M[0-9]+{_OPTIONAL_EXTENSION}")),
    ("tables", re.compile(rf".+-appb-T[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf".+-appb-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf".+-jpbibl-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf".+-jpfolb-I[0-9]+{_OPTIONAL_EXTENSION}")),
    (
        "other-images",
        re.compile(rf"JPOXMLDOC[0-9]+-poat-I[0-9]+{_OPTIONAL_EXTENSION}"),
    ),
    ("other-images", re.compile(rf"JPOXMLDOC[0-9]+-biod-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"JPOXMLDOC[0-9]+-lacs-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"JPOXMLDOC[0-9]+-jpothd-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"[0-9]-jpseql-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"JPOXMLDOC01-jpseql-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"JPOXMLDOC01-jpatta-I[0-9]+{_OPTIONAL_EXTENSION}")),
    ("other-images", re.compile(rf"[0-9]+-jpntce-I[0-9]+{_OPTIONAL_EXTENSION}")),
)


def detect_image_kind(
    image_name: str,
) -> IMAGE_KIND:
    """detect image kind from image name

    Args:
        image_name (str): image name"""
    for kind, pattern in _KIND_RULES:
        if pattern.fullmatch(image_name):
            return kind
    return "unknown"
