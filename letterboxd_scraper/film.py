from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import requests

from .config import POSTER_DIR, IMG_DIM

class Film:
    def __init__(self, film_title, film_year, film_slug):
        self.film_title: str = film_title
        self.film_year: int | None = film_year
        self.film_slug: str = film_slug
        self._poster_url: str | None = None
        self._poster_img = None

    @property
    def poster_url(self) -> str:
        if self._poster_url is not None:
            return self._poster_url
        print(f"Fetching poster url for {self.film_slug}")
        res = requests.get(f"https://letterboxd.com/ajax/poster/film/{self.film_slug}/std/{IMG_DIM.width}x{IMG_DIM.height}/")
        soup = BeautifulSoup(res.text, "html.parser")
        self._poster_url = soup.find("img", class_="image")["src"]
        return self._poster_url

    @property
    def poster_image(self):
        if self._poster_img is not None:
            return self._poster_img

        # check if image is available locally
        img = Path(POSTER_DIR / f"{self.film_slug}_{self.poster_url[-10:]}.jpg")
        if img.is_file():
            print(f"Image for {self.film_slug} is available locally")
            return Image.open(img)

        print(f"Fetching image from {self.poster_url}")
        res = requests.get(self.poster_url)
        if res.headers["Content-Type"] == "image/jpeg":
            img = Image.open(BytesIO(res.content))
            img.save(
                POSTER_DIR / f"{self.film_slug}_{self.poster_url[-10:]}.jpg"
            )
            self._poster_img = img
            return img
        else:
            print(f"No image available for {self.film_slug}")
            img = Image.new(
                mode="RGB",
                size=(IMG_DIM.width, IMG_DIM.height),
                color="gray"
            )
            # TODO: Fix text overflowing in the image
            font = ImageFont.truetype("arial.ttf", size=24)
            film_title = f"{self.film_title}"
            if self.film_year: film_title += f" ({self.film_year})"
            ImageDraw.Draw(img).text(
                xy=(IMG_DIM.width/2, IMG_DIM.height/2),
                text=film_title,
                fill="white",
                anchor="mm",
                font=font
            )

            self._poster_img = img
            return img

    def __repr__(self):
        return f"Film(film_title={self.film_title}, film_year={self.film_year})"

class DiaryEntry(Film):
    def __init__(self, date, film_title, film_year, rating, like, rewatch, film_slug):
        super().__init__(film_title, film_year, film_slug)
        self.date = date
        self.rating = rating
        self.like = like
        self.rewatch = rewatch

    def __repr__(self):
        return f"DiaryEntry(date={self.date}, film_title={self.film_title})"
