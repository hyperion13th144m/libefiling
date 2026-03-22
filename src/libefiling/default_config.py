from .image.params import ImageAttribute, ImageConvertParam

defaultImageParams = [
    ImageConvertParam(
        width=300,
        height=300,
        suffix="-thumbnail",
        format=".webp",
        attributes=[ImageAttribute(key="sizeTag", value="thumbnail")],
    ),
    ImageConvertParam(
        width=600,
        height=600,
        suffix="-middle",
        format=".webp",
        attributes=[ImageAttribute(key="sizeTag", value="middle")],
    ),
    ImageConvertParam(
        width=800,
        height=0,
        suffix="-large",
        format=".webp",
        attributes=[ImageAttribute(key="sizeTag", value="large")],
    ),
]
