from libefiling.manifest import Manifest


def get_document_code(file_path: str) -> str | None:
    """Get document code from manifest, archive or procedure file

    Args:
        file_path (str): manifest, archive or procedure file path
    Returns:
        str: document code (e.g. A163) or None if not found
    """
    if file_path.endswith("manifest.json"):
        return get_document_code_from_manifest(file_path)
    else:
        return get_document_code_from_filename(file_path)


def get_document_code_from_manifest(manifest_path: str) -> str | None:
    """Get document code from manifest file path

    Args:
        manifest_path (str): manifest file path
    Returns:
        str: document code (e.g. A163) or None if not found
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = Manifest.model_validate(f.read())
    return manifest.document.code if manifest.document.code else None



def get_document_code_from_filename(file_path: str) -> str | None:
    """Get document code from archive file name

    Args:
        file_path (str): archive file path
    Returns:
        str: document code (e.g. A163) or None if not found
    """
    if len(file_path) < 29:
        return None
    else:
        return file_path[20:20 + 9].replace("_", "").strip()

if __name__ == "__main__":
    import sys

    print(get_document_code(sys.argv[1]))
