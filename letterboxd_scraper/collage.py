import concurrent.futures
from operator import attrgetter
import sys

from PIL import Image

from .config import IMG_DIM

class Collage:
    def __init__(self, user):
        self.user = user # LetterboxdUser instance
        self.image = None

    def __repr__(self):
        return f"Collage(username={self.user})"

    def create(self, size: tuple[int, int]=(5, 5)):
        """Creates the collage from user's diary. Returns a PIL Image"""
        cols, rows = size

        if cols * rows > 100:
            raise ValueError("Maximum size of collage is 10x10")

        print(f"Creating {cols}x{rows} collage...")
        
        diary_entries = self.user.diary(page=1)
        if not diary_entries:
            raise ValueError(f"No diary entries found for user {self.user.username}")
            
        if cols * rows > 50 and len(diary_entries) < cols * rows:
            page2_entries = self.user.diary(page=2)
            if page2_entries:
                diary_entries.extend(page2_entries)

        needed_entries = cols * rows
        if len(diary_entries) < needed_entries:
            print(f"Warning: Only found {len(diary_entries)} entries, but need {needed_entries}")
            print("Will create smaller collage or use placeholders")

        # Ensure we have enough entries
        entries_to_use = diary_entries[:needed_entries]
        
        print(f"Fetching {len(entries_to_use)} poster images...")
        
        # Use ThreadPoolExecutor with error handling
        images = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_entry = {
                executor.submit(lambda entry: entry.poster_image, entry): entry 
                for entry in entries_to_use
            }
            
            for future in concurrent.futures.as_completed(future_to_entry):
                entry = future_to_entry[future]
                try:
                    image = future.result()
                    images.append(image)
                except Exception as e:
                    print(f"Error fetching image for {entry.film_title}: {e}")
                    # Create placeholder
                    placeholder = Image.new("RGB", (IMG_DIM.width, IMG_DIM.height), color="gray")
                    images.append(placeholder)

        # If we still don't have enough images, create placeholders
        while len(images) < needed_entries:
            placeholder = Image.new("RGB", (IMG_DIM.width, IMG_DIM.height), color="gray")
            images.append(placeholder)

        print(f"Creating collage with {len(images)} images...")
        
        collage_width = cols * IMG_DIM.width
        collage_height = rows * IMG_DIM.height
        collage = Image.new("RGB", (collage_width, collage_height))
        
        for row in range(rows):
            for col in range(cols):
                i = row * cols + col
                if i < len(images):
                    try:
                        collage.paste(
                            images[i],
                            (col * IMG_DIM.width, row * IMG_DIM.height)
                        )
                    except Exception as e:
                        print(f"Error pasting image at position {i}: {e}")
                        # Paste a placeholder
                        placeholder = Image.new("RGB", (IMG_DIM.width, IMG_DIM.height), color="gray")
                        collage.paste(placeholder, (col * IMG_DIM.width, row * IMG_DIM.height))
        
        self.image = collage
        print("Collage created successfully!")
        return collage
