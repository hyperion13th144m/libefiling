from pathlib import Path

from PIL import Image, ImageChops, ImageOps


def convert_image(
    src_image: Path, dst_image: Path, width: int, height: int
) -> tuple[int, int]:
    """convert src_images and save as dst_image.

    Args:
        src_image (Path): source image path
        dst_image (Path): destination image path
        width (int): target width
        height (int): target height
    """

    ### 画像変換の実行
    converted_image = convert(src_image, width, height)
    converted_image.save(dst_image)

    return (converted_image.width, converted_image.height)


def convert(src: Path, width: int, height: int) -> Image.Image:
    image = Image.open(str(src))

    # convert a monochrome image to grayscale.
    if image.mode == "1":
        image = image.convert("L")

    # remove margins
    image = crop(image)

    # resize
    resize_size = get_size(image, width, height)
    resized_image = image.resize(resize_size, resample=Image.Resampling.LANCZOS)

    # expand image to fit given width and height.
    dw = width - resized_image.width if width > 0 else 0
    dh = height - resized_image.height if height > 0 else 0
    if dw > 0 or dh > 0:
        padding = (dw // 2, dh // 2, dw - (dw // 2), dh - (dh // 2))
        new_image = ImageOps.expand(resized_image, padding, 255)
        return new_image
    else:
        return resized_image


def crop(image: Image.Image):
    # background image
    bg = Image.new(image.mode, image.size, 255)  # image.getpixel((0, 0)))

    # difference original image and background image.
    diff = ImageChops.difference(image, bg)
    # diff = diff.filter(ImageFilter.MedianFilter(5))  too slow
    # diff = diff.point(lambda p: 255 if p > 160 else 0)

    # detect boundary to background color
    croprange = diff.getbbox()
    crop_image = image.crop(croprange)

    return crop_image


def get_size(image: Image.Image, width: int, height: int):
    x_ratio = width / image.width
    y_ratio = height / image.height

    if width == 0:
        resize_size = (round(image.width * y_ratio), height)
    elif height == 0:
        resize_size = (width, round(image.height * x_ratio))
    elif x_ratio < y_ratio:
        resize_size = (width, round(image.height * x_ratio))
    else:
        resize_size = (round(image.width * y_ratio), height)

    return resize_size
