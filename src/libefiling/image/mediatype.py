"""Media type detection from file extensions."""


def get_media_type(extension: str) -> str:
    """Get media type from file extension.

    Args:
        extension: File extension (with or without leading dot)

    Returns:
        Media type string (e.g., "image/webp", "application/xml")

    Examples:
        >>> get_media_type("webp")
        'image/webp'
        >>> get_media_type(".jpg")
        'image/jpeg'
        >>> get_media_type("xml")
        'application/xml'
    """
    # Remove leading dot if present
    ext = extension.lstrip(".").lower()

    # Mapping of extensions to media types
    media_type_map = {
        "webp": "image/webp",
        "tif": "image/tiff",
        "tiff": "image/tiff",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "xml": "application/xml",
    }

    return media_type_map.get(ext, "application/octet-stream")
