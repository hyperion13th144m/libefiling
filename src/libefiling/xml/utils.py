from pathlib import Path
from xml.etree import ElementTree as ET

from libefiling.manifest import Manifest


def get_document_code(manifest_path: str) -> str | None:
    """Get document code from manifest file

    Args:
        manifest_path (str): manifest file path (e.g. manifest.json)
    Returns:
        str: document code (e.g. A163)
    """
    mp = Path(manifest_path)
    manifest = Manifest.model_validate_json(mp.read_text(encoding="utf-8"))
    manifest_dir = mp.parent
    xml_dir = manifest_dir / manifest.paths.xml_dir
    for xml in manifest.xml_files:
        if xml.kind == "procedure":
            return get_document_code_from_procedure(str(xml_dir / xml.filename))
    else:
        return None


def get_document_code_from_procedure(procedure_path: str) -> str | None:
    """Get document code from procedure.xml file path

    Args:
        procedure_path (str): procedure.xml file path
    Returns:
        str: document code (e.g. A163)
    """
    ns = {"jp": "http://www.jpo.go.jp"}
    tree = ET.parse(procedure_path)
    elem = tree.find(".//jp:document-name", ns)
    if elem is None:
        return None

    # Namespaced attributes are stored as expanded QName keys.
    code = elem.get("{http://www.jpo.go.jp}document-code")
    return code.strip() if code else None


if __name__ == "__main__":
    import sys

    print(get_document_code(sys.argv[1]))
