import xml.etree.ElementTree as ET
from typing import List

from libefiling.manifest import ImageEntry


def save_as_xml(image_entries: List[ImageEntry], file_path: str):
    root = ET.Element("images")
    for entry in image_entries:
        for derived in entry.derived:
            elem = ET.Element(
                "image",
                {
                    "orig-path": entry.original.path,
                    "orig-filename": entry.original.path.split("/")[-1],
                    "new": derived.path,
                    "width": str(derived.width),
                    "height": str(derived.height),
                    "kind": entry.kind,
                    **{attr.key: attr.value for attr in derived.attributes},
                },
            )
            root.append(elem)
    ET.indent(root, space="  ")
    tree = ET.ElementTree(root)
    tree.write(file_path, encoding="utf-8", xml_declaration=True)
