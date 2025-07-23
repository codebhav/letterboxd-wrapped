from io import BytesIO
from pathlib import Path
import platform

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

    def _get_font(self, size=24):
        """Get appropriate font based on operating system"""
        try:
            system = platform.system()
            if system == "Windows":
                return ImageFont.truetype("arial.ttf", size=size)
            elif system == "Darwin":  # macOS
                return ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size=size)
            else:  # Linux and others
                # Try common font paths
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf", 
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
                for font_path in font_paths:
                    if Path(font_path).exists():
                        return ImageFont.truetype(font_path, size=size)
                # Fallback to default font
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    @property
    def poster_url(self) -> str:
        if self._poster_url is not None:
            return self._poster_url
        
        try:
            print(f"Fetching poster url for {self.film_slug}")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            res = requests.get(
                f"https://letterboxd.com/ajax/poster/film/{self.film_slug}/std/{IMG_DIM.width}x{IMG_DIM.height}/",
                headers=headers,
                timeout=10
            )
            res.raise_for_status()
            soup = BeautifulSoup(res.text, "html.parser")
            img_tag = soup.find("img", class_="image")
            if img_tag and img_tag.get("src"):
                self._poster_url = img_tag["src"]
                return self._poster_url
            else:
                print(f"No poster found for {self.film_slug}")
                return None
        except Exception as e:
            print(f"Error fetching poster URL for {self.film_slug}: {e}")
            return None

    @property
    def poster_image(self):
        if self._poster_img is not None:
            return self._poster_img

        # Check if image is available locally
        poster_url = self.poster_url
        if poster_url:
            img_filename = f"{self.film_slug}_{poster_url[-10:]}.jpg"
            img_path = POSTER_DIR / img_filename
            
            if img_path.is_file():
                print(f"Image for {self.film_slug} is available locally")
                try:
                    self._poster_img = Image.open(img_path)
                    return self._poster_img
                except Exception as e:
                    print(f"Error opening local image: {e}")

            # Download image
            try:
                print(f"Fetching image from {poster_url}")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                res = requests.get(poster_url, headers=headers, timeout=10)
                res.raise_for_status()
                
                if res.headers.get("Content-Type", "").startswith("image/"):
                    img = Image.open(BytesIO(res.content))
                    img = img.convert('RGB')  # Ensure RGB format
                    img.save(img_path, "JPEG")
                    self._poster_img = img
                    return img
            except Exception as e:
                print(f"Error downloading image for {self.film_slug}: {e}")

        # Create placeholder image
        print(f"Creating placeholder for {self.film_slug}")
        img = Image.new(
            mode="RGB",
            size=(IMG_DIM.width, IMG_DIM.height),
            color="gray"
        )
        
        try:
            font = self._get_font(size=16)
            film_title = f"{self.film_title}"
            if self.film_year: 
                film_title += f" ({self.film_year})"
            
            # Word wrap text to fit image
            words = film_title.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + " " + word if current_line else word
                bbox = font.getbbox(test_line)
                if bbox[2] <= IMG_DIM.width - 20:  # 10px margin on each side
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                        current_line = word
                    else:
                        lines.append(word)
            
            if current_line:
                lines.append(current_line)
            
            # Limit to max 3 lines
            lines = lines[:3]
            
            # Calculate starting y position to center text
            line_height = font.getbbox("A")[3] + 5
            total_height = len(lines) * line_height
            start_y = (IMG_DIM.height - total_height) // 2
            
            draw = ImageDraw.Draw(img)
            for i, line in enumerate(lines):
                bbox = font.getbbox(line)
                x = (IMG_DIM.width - bbox[2]) // 2
                y = start_y + i * line_height
                draw.text((x, y), line, fill="white", font=font)
                
        except Exception as e:
            print(f"Error creating text for placeholder: {e}")

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
