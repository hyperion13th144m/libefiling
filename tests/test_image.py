import glob
import sys

from libefiling.image.convert import convert_image
from libefiling.image.params import ImageConvertParam

params = [
    ImageConvertParam(
        width=300,
        height=300,
        suffix="-thumbnail",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "thumbnail"}],
    ),
    ImageConvertParam(
        width=600,
        height=600,
        suffix="-middle",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "middle"}],
    ),
    ImageConvertParam(
        width=800,
        height=0,
        suffix="-large",
        format=".webp",
        attributes=[{"key": "sizeTag", "value": "large"}],
    ),
]

if __name__ == "__main__":
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
            params=params,
        )
    result.save_as_xml(dst_dir + "/conversion_results.xml")
