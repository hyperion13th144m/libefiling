import glob
import sys

from libefiling.image.convert import convert_image
from libefiling.image.mediatype import get_media_type


def test_get_media_type():
    """Test media type detection from file extensions."""
    assert get_media_type("webp") == "image/webp"
    assert get_media_type(".webp") == "image/webp"
    assert get_media_type("tif") == "image/tiff"
    assert get_media_type("tiff") == "image/tiff"
    assert get_media_type(".tiff") == "image/tiff"
    assert get_media_type("jpg") == "image/jpeg"
    assert get_media_type(".jpg") == "image/jpeg"
    assert get_media_type("jpeg") == "image/jpeg"
    assert get_media_type("gif") == "image/gif"
    assert get_media_type("xml") == "application/xml"
    assert get_media_type(".xml") == "application/xml"
    # Unknown extension should return default
    assert get_media_type("unknown") == "application/octet-stream"
    print("All media type tests passed!")


if __name__ == "__main__":
    # Run tests
    test_get_media_type()
    
    if len(sys.argv) != 3:
        print("Usage: python test_image.py <src_dir> <dst_dir>")
        sys.exit(1)

    src_dir = sys.argv[1]
    dst_dir = sys.argv[2]
    src_images = glob.glob(f"{src_dir}/*.tif") + glob.glob(f"{src_dir}/*.jpg")
    for src_image in src_images:
        result = convert_image(
            src_image,
            dst_dir,
            params=[
                {
                    "width": 300,
                    "height": 300,
                    "suffix": "-thumbnail",
                    "format": ".webp",
                    "attributes": [{"key": "sizeTag", "value": "thumbnail"}],
                },
                {
                    "width": 600,
                    "height": 600,
                    "suffix": "-middle",
                    "format": ".webp",
                    "attributes": [{"key": "sizeTag", "value": "middle"}],
                },
                {
                    "width": 800,
                    "height": 0,
                    "suffix": "-large",
                    "format": ".webp",
                    "attributes": [{"key": "sizeTag", "value": "large"}],
                },
            ],
        )
    result.save_as_xml(dst_dir + "/conversion_results.xml")
