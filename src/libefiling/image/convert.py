from pathlib import Path

from PIL import Image, ImageOps

WHITE_THRESHOLD = 250
FOREGROUND_LUT = [255 if value < WHITE_THRESHOLD else 0 for value in range(256)]
REDUCING_GAP = 3.0


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
    prepared_image = load_image(src_image)
    converted_image = convert_prepared(prepared_image, width, height)
    converted_image.save(dst_image)

    return (converted_image.width, converted_image.height)


def convert(src: Path, width: int, height: int) -> Image.Image:
    return convert_prepared(load_image(src), width, height)


def load_image(src: Path) -> Image.Image:
    # multiprocessing環境下でのデッドロックを回避するため、
    # 画像を開いた直後にload()を呼び出してファイルを閉じる
    image = Image.open(str(src))
    image.load()  # 画像データをメモリに読み込み、ファイルを閉じる

    # convert a monochrome image to grayscale.
    if image.mode == "1":
        image = image.convert("L")

    # remove margins
    return crop(image)


def convert_prepared(image: Image.Image, width: int, height: int) -> Image.Image:
    if width == 0 and height == 0:
        raise ValueError("width and height cannot both be zero")

    # resize
    resize_size = get_size(image, width, height)
    if resize_size == image.size:
        resized_image = image.copy()
    else:
        resize_ratio = max(image.width / resize_size[0], image.height / resize_size[1])
        reducing_gap = REDUCING_GAP if resize_ratio > 1 else None
        resized_image = image.resize(
            resize_size,
            resample=Image.Resampling.LANCZOS,
            reducing_gap=reducing_gap,
        )

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
    crop_box = get_crop_box(image)
    if crop_box is None or crop_box == (0, 0, image.width, image.height):
        return image

    return image.crop(crop_box)


def get_crop_box(image: Image.Image):
    grayscale = image if image.mode == "L" else image.convert("L")
    mask = grayscale.point(FOREGROUND_LUT, mode="1")
    return mask.getbbox()


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
