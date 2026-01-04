from .image.params import ImageConvertParam

defaultImageParams: list[ImageConvertParam] = [
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
]
