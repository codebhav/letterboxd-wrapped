# letterboxd_scraper/wrapped.py
import random
import math
from datetime import datetime, timedelta
from calendar import month_name
import platform
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests

from .config import IMG_DIM

class LetterboxdWrapped:
    def __init__(self, user, month=None, year=None):
        self.user = user
        self.month = month or datetime.now().month
        self.year = year or datetime.now().year  # Back to current year since user has 2025 entries
        self.month_name = month_name[self.month]
        
        # Instagram Story dimensions
        self.width = 1080
        self.height = 1920
        
        # Colors inspired by the reference
        self.bg_color = "#F5D908"  # Yellow background
        self.text_color = "#1A1A1A"  # Dark text
        
    def _get_font(self, size=40, bold=False):
        """Get appropriate font based on operating system"""
        try:
            system = platform.system()
            if system == "Windows":
                font_name = "arialbd.ttf" if bold else "arial.ttf"
                return ImageFont.truetype(font_name, size=size)
            elif system == "Darwin":  # macOS
                font_path = "/System/Library/Fonts/Arial.ttf"
                if bold:
                    font_path = "/System/Library/Fonts/Arial Bold.ttf"
                return ImageFont.truetype(font_path, size=size)
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
                ]
                for font_path in font_paths:
                    if Path(font_path).exists():
                        return ImageFont.truetype(font_path, size=size)
                return ImageFont.load_default()
        except Exception:
            return ImageFont.load_default()

    def _get_monthly_diary_entries(self):
        """Get diary entries for the specified month and year"""
        all_entries = []
        
        # Get entries from multiple pages if needed
        for page in range(1, 6):  # Check up to 5 pages
            entries = self.user.diary(page=page)
            if not entries:
                break
            all_entries.extend(entries)
        
        print(f"Found {len(all_entries)} total diary entries")
        
        # Debug: show first few entries
        if all_entries:
            print("Sample entry dates:")
            for i, entry in enumerate(all_entries[:5]):
                print(f"  {entry.date} - {entry.film_title}")
        
        # Filter by month and year
        monthly_entries = []
        target_month_name = month_name[self.month]
        
        # Month name mappings (both full and abbreviated)
        month_mappings = {
            'january': 1, 'jan': 1,
            'february': 2, 'feb': 2,
            'march': 3, 'mar': 3,
            'april': 4, 'apr': 4,
            'may': 5,
            'june': 6, 'jun': 6,
            'july': 7, 'jul': 7,
            'august': 8, 'aug': 8,
            'september': 9, 'sep': 9,
            'october': 10, 'oct': 10,
            'november': 11, 'nov': 11,
            'december': 12, 'dec': 12
        }
        
        for entry in all_entries:
            try:
                # Parse date (format: "YYYY-Month-DD")
                date_parts = entry.date.split('-')
                if len(date_parts) >= 3:
                    entry_year = int(date_parts[0])
                    entry_month_name = date_parts[1].lower()
                    
                    # Convert month name to number (handle both full and abbreviated)
                    entry_month = month_mappings.get(entry_month_name)
                    
                    # Debug output
                    if entry_month == self.month:
                        print(f"Found {target_month_name} entry: {entry.date} - {entry.film_title} (Year: {entry_year})")
                    
                    if entry_year == self.year and entry_month == self.month:
                        monthly_entries.append(entry)
            except (ValueError, IndexError) as e:
                print(f"Error parsing date '{entry.date}': {e}")
                continue
        
        print(f"Found {len(monthly_entries)} entries for {target_month_name} {self.year}")
        return monthly_entries

    def _create_dynamic_layout(self, images, num_posters=15):
        """Create a dynamic layout similar to the reference images"""
        layout_positions = []
        
        # Base poster size (smaller for more dynamic look)
        base_width = 140
        base_height = int(base_width * 1.5)  # Movie poster aspect ratio
        
        # Define zones for placement (avoiding header and footer areas)
        header_height = 400
        footer_height = 200
        available_height = self.height - header_height - footer_height
        
        # Create a grid-based system but with random variations
        cols = 6
        rows = 8
        cell_width = self.width // cols
        cell_height = available_height // rows
        
        used_cells = set()
        
        for i in range(min(num_posters, len(images))):
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                # Random size variation
                size_multiplier = random.uniform(0.8, 1.4)
                poster_width = int(base_width * size_multiplier)
                poster_height = int(base_height * size_multiplier)
                
                # Random position within grid cells
                col = random.randint(0, cols - 1)
                row = random.randint(0, rows - 1)
                
                # Skip if this area is too crowded
                cell_key = f"{col},{row}"
                if cell_key in used_cells:
                    attempts += 1
                    continue
                
                # Calculate position with some randomness
                x = col * cell_width + random.randint(-30, 30)
                y = header_height + row * cell_height + random.randint(-20, 20)
                
                # Ensure poster fits within bounds
                if x + poster_width > self.width:
                    x = self.width - poster_width - 10
                if y + poster_height > self.height - footer_height:
                    y = self.height - footer_height - poster_height - 10
                if x < 10:
                    x = 10
                if y < header_height:
                    y = header_height
                
                # Random rotation for more dynamic look
                rotation = random.randint(-15, 15)
                
                layout_positions.append({
                    'x': x,
                    'y': y,
                    'width': poster_width,
                    'height': poster_height,
                    'rotation': rotation
                })
                
                # Mark surrounding cells as used
                for dc in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        used_cells.add(f"{col + dc},{row + dr}")
                
                break
                
            if attempts >= 50:
                # Fallback position
                x = random.randint(10, self.width - base_width - 10)
                y = random.randint(header_height, self.height - footer_height - base_height)
                layout_positions.append({
                    'x': x,
                    'y': y,
                    'width': base_width,
                    'height': base_height,
                    'rotation': 0
                })
        
        return layout_positions

    def _resize_and_rotate_image(self, image, width, height, rotation):
        """Resize image and apply rotation"""
        # Resize image
        resized = image.resize((width, height), Image.Resampling.LANCZOS)
        
        # Apply rotation if needed
        if rotation != 0:
            # Rotate with expand=True to avoid cropping
            rotated = resized.rotate(rotation, expand=True, fillcolor=(0, 0, 0, 0))
            return rotated
        
        return resized

    def _draw_heart_icon(self, draw, x, y, size=30):
        """Draw a simple heart icon"""
        # Heart shape using curves (simplified)
        heart_color = "#E50914"  # Netflix red-ish color
        
        # Create heart shape with circles and triangle
        left_circle = (x, y, x + size//2, y + size//2)
        right_circle = (x + size//2, y, x + size, y + size//2)
        
        # Draw circles for top of heart
        draw.ellipse(left_circle, fill=heart_color)
        draw.ellipse(right_circle, fill=heart_color)
        
        # Draw triangle for bottom of heart
        triangle_points = [
            (x, y + size//3),
            (x + size, y + size//3),
            (x + size//2, y + size)
        ]
        draw.polygon(triangle_points, fill=heart_color)

    def create(self):
        """Create the Instagram Story wrapped image"""
        print(f"Creating Letterboxd Wrapped for {self.month_name} {self.year}...")
        
        # Get monthly entries
        monthly_entries = self._get_monthly_diary_entries()
        
        if not monthly_entries:
            raise ValueError(f"No diary entries found for {self.month_name} {self.year}")
        
        print(f"Found {len(monthly_entries)} movies watched in {self.month_name} {self.year}")
        
        # Create base image
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Get poster images (limit to reasonable number for layout)
        num_posters = min(20, len(monthly_entries))
        poster_images = []
        
        print(f"Fetching {num_posters} poster images...")
        for i, entry in enumerate(monthly_entries[:num_posters]):
            try:
                poster = entry.poster_image
                if poster:
                    poster_images.append(poster)
                print(f"Fetched {i+1}/{num_posters}: {entry.film_title}")
            except Exception as e:
                print(f"Error fetching poster for {entry.film_title}: {e}")
                continue
        
        if not poster_images:
            raise ValueError("No poster images could be fetched")
        
        # Create dynamic layout
        layout_positions = self._create_dynamic_layout(poster_images)
        
        # Draw movie posters
        temp_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        
        for i, (image, pos) in enumerate(zip(poster_images, layout_positions)):
            try:
                # Resize and rotate poster
                processed_poster = self._resize_and_rotate_image(
                    image, pos['width'], pos['height'], pos['rotation']
                )
                
                # Calculate position for rotated image
                paste_x = pos['x'] - (processed_poster.width - pos['width']) // 2
                paste_y = pos['y'] - (processed_poster.height - pos['height']) // 2
                
                # Add subtle drop shadow
                shadow_offset = 3
                shadow_img = Image.new('RGBA', processed_poster.size, (0, 0, 0, 50))
                temp_img.paste(shadow_img, (paste_x + shadow_offset, paste_y + shadow_offset), shadow_img)
                
                # Paste the poster
                if processed_poster.mode == 'RGBA':
                    temp_img.paste(processed_poster, (paste_x, paste_y), processed_poster)
                else:
                    temp_img.paste(processed_poster, (paste_x, paste_y))
                    
            except Exception as e:
                print(f"Error placing poster {i}: {e}")
                continue
        
        # Composite the posters onto the background
        img = Image.alpha_composite(img.convert('RGBA'), temp_img).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Draw header text
        try:
            # Main title
            title_font = self._get_font(50, bold=True)
            title_text = "LETTERBOXD WRAPPED"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, 80), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle
            subtitle_font = self._get_font(60, bold=True)
            subtitle_text = f"{self.month_name.upper()} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            draw.text((subtitle_x, 150), subtitle_text, fill=self.text_color, font=subtitle_font)
            
            # Count text
            count_font = self._get_font(70, bold=False)
            count_text = f"I watched {len(monthly_entries)} movies."
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_x = (self.width - count_width) // 2
            draw.text((count_x, 250), count_text, fill=self.text_color, font=count_font)
            
        except Exception as e:
            print(f"Error drawing text: {e}")
        
        # Draw heart icon at bottom
        try:
            heart_size = 40
            heart_x = (self.width - heart_size) // 2
            heart_y = self.height - 120
            self._draw_heart_icon(draw, heart_x, heart_y, heart_size)
        except Exception as e:
            print(f"Error drawing heart icon: {e}")
        
        print("Letterboxd Wrapped image created successfully!")
        return img
