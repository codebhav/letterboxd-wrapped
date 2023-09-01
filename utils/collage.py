from io import BytesIO
from PIL import Image
import requests


def create_collage(image_urls: list[str]) -> BytesIO:
    # TODO: only fetch images that are going to be used
    imgs = [get_img_from_url(i) for i in image_urls]

    # 5x5 grid collage
    collage_width = 5 * imgs[0].width
    collage_height = 5 * imgs[0].height
    collage = Image.new("RGB", (collage_width, collage_height))

    # TODO: options to have different grid sizes, not just 5x5
    for row in range(5):
        for col in range(5):
            index = row * 5 + col
            if index < len(imgs):
                collage.paste(imgs[index], (col * imgs[0].width, row * imgs[0].height))

    collage_bytesio = BytesIO()
    collage.save(collage_bytesio, format="JPEG")
    collage_bytesio.seek(0)
    return collage_bytesio


def get_img_from_url(url: str):
    """Creates a PIL image from url"""
    print(f"Getting image from {url}")
    res = requests.get(url)
    if res.headers["Content-Type"] == "image/jpeg":
        return Image.open(BytesIO(res.content))
