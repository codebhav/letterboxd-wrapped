# letterboxd_scraper/wrapped.py - Updated with grid layout
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
        self.year = year or datetime.now().year
        self.month_name = month_name[self.month]
        
        # Instagram Story dimensions
        self.width = 1080
        self.height = 1920
        
        # Letterboxd brand colors
        self.bg_color = "#14181C"  # Letterboxd's dark blue-gray background
        self.text_color = "#FFFFFF"  # White text
        self.accent_color = "#FF8000"  # Letterboxd's signature orange
        
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

    def _create_grid_layout(self, images, max_posters=36):
        """Create a clean grid layout like the NYT reference"""
        layout_positions = []
        
        # Limit number of posters for clean grid
        num_posters = min(len(images), max_posters)
        
        # Define available space (avoiding header and footer)
        header_height = 280  # Space for title and subtitle
        footer_height = 120  # Space for heart icon
        available_height = self.height - header_height - footer_height
        
        # Calculate optimal grid dimensions
        # Try different grid configurations to find the best fit
        best_config = None
        best_poster_size = 0
        
        for cols in range(4, 8):  # Try 4-7 columns
            rows = math.ceil(num_posters / cols)
            
            # Calculate poster size with margins
            margin = 15  # Space between posters
            side_margin = 40  # Margin from screen edges
            
            available_width = self.width - (2 * side_margin)
            poster_width = (available_width - (cols - 1) * margin) / cols
            poster_height = poster_width * 1.5  # Movie poster aspect ratio
            
            total_grid_height = rows * poster_height + (rows - 1) * margin
            
            # Check if this configuration fits and is better than previous
            if total_grid_height <= available_height and poster_width > best_poster_size:
                best_config = {
                    'cols': cols,
                    'rows': rows,
                    'poster_width': poster_width,
                    'poster_height': poster_height,
                    'margin': margin,
                    'side_margin': side_margin,
                    'total_grid_height': total_grid_height
                }
                best_poster_size = poster_width
        
        if not best_config:
            # Fallback: force a 6x6 grid with smaller posters
            best_config = {
                'cols': 6,
                'rows': 6,
                'poster_width': 140,
                'poster_height': 210,
                'margin': 12,
                'side_margin': 30,
                'total_grid_height': 6 * 210 + 5 * 12
            }
        
        # Calculate starting position to center the grid
        start_x = best_config['side_margin']
        start_y = header_height + (available_height - best_config['total_grid_height']) // 2
        
        # Create grid positions
        for i in range(num_posters):
            row = i // best_config['cols']
            col = i % best_config['cols']
            
            x = start_x + col * (best_config['poster_width'] + best_config['margin'])
            y = start_y + row * (best_config['poster_height'] + best_config['margin'])
            
            # Add slight random variation to avoid looking too rigid
            # But keep it subtle to maintain grid structure
            random_x = random.randint(-3, 3)
            random_y = random.randint(-3, 3)
            
            layout_positions.append({
                'x': int(x + random_x),
                'y': int(y + random_y),
                'width': int(best_config['poster_width']),
                'height': int(best_config['poster_height']),
                'rotation': random.randint(-2, 2),  # Very subtle rotation
                'z_index': i
            })
        
        print(f"Created grid layout: {best_config['cols']}x{best_config['rows']} with {num_posters} posters")
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
        """Draw a simple heart icon with Letterboxd orange"""
        # Heart shape using Letterboxd's signature orange
        heart_color = "#FF8000"  # Letterboxd orange
        
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
        
        # Set random seed based on username and month for consistent but varied layouts
        import hashlib
        seed_string = f"{self.user.username}{self.month}{self.year}"
        seed = int(hashlib.md5(seed_string.encode()).hexdigest()[:8], 16)
        random.seed(seed)
        
        # Get monthly entries
        monthly_entries = self._get_monthly_diary_entries()
        
        if not monthly_entries:
            raise ValueError(f"No diary entries found for {self.month_name} {self.year}")
        
        print(f"Found {len(monthly_entries)} movies watched in {self.month_name} {self.year}")
        
        # Create base image
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Get poster images
        poster_images = []
        
        print(f"Fetching poster images...")
        for i, entry in enumerate(monthly_entries):
            try:
                poster = entry.poster_image
                if poster:
                    poster_images.append(poster)
                print(f"Fetched {i+1}/{len(monthly_entries)}: {entry.film_title}")
            except Exception as e:
                print(f"Error fetching poster for {entry.film_title}: {e}")
                continue
        
        if not poster_images:
            raise ValueError("No poster images could be fetched")
        
        # Create grid layout (changed from dynamic layout)
        layout_positions = self._create_grid_layout(poster_images)
        
        # Draw movie posters in grid
        for i, pos in enumerate(layout_positions):
            if i >= len(poster_images):
                break
                
            try:
                image = poster_images[i]
                
                # Resize and rotate poster (minimal rotation for grid)
                processed_poster = self._resize_and_rotate_image(
                    image, pos['width'], pos['height'], pos['rotation']
                )
                
                # Calculate position for rotated image
                paste_x = pos['x'] - (processed_poster.width - pos['width']) // 2
                paste_y = pos['y'] - (processed_poster.height - pos['height']) // 2
                
                # Add subtle drop shadow and border for dark theme
                shadow_offset = 3
                shadow_color = (0, 0, 0, 80)  # Stronger shadow for dark background
                
                # Create shadow
                shadow_img = Image.new('RGBA', processed_poster.size, shadow_color)
                
                # Paste shadow first
                if processed_poster.mode == 'RGBA':
                    img.paste(shadow_img, (paste_x + shadow_offset, paste_y + shadow_offset), shadow_img)
                    img.paste(processed_poster, (paste_x, paste_y), processed_poster)
                else:
                    # Convert to RGBA for proper alpha blending
                    temp_img = Image.new('RGBA', img.size, (0, 0, 0, 0))
                    temp_img.paste(img, (0, 0))
                    temp_img.paste(shadow_img, (paste_x + shadow_offset, paste_y + shadow_offset), shadow_img)
                    temp_img.paste(processed_poster, (paste_x, paste_y))
                    img = temp_img.convert('RGB')
                
                # Add subtle orange border to enhance Letterboxd aesthetic
                draw_temp = ImageDraw.Draw(img)
                border_color = self.accent_color
                border_width = 1
                draw_temp.rectangle(
                    [paste_x - border_width, paste_y - border_width, 
                     paste_x + pos['width'] + border_width, paste_y + pos['height'] + border_width],
                    outline=border_color,
                    width=border_width
                )
                    
            except Exception as e:
                print(f"Error placing poster {i}: {e}")
                continue
        
        # Redraw to ensure we have the right draw object
        draw = ImageDraw.Draw(img)
        
        # Draw header text with Letterboxd styling
        try:
            # Main title
            title_font = self._get_font(45, bold=True)
            title_text = "LETTERBOXD WRAPPED"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, 50), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle with orange accent
            subtitle_font = self._get_font(50, bold=True)
            subtitle_text = f"{self.month_name.upper()} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            draw.text((subtitle_x, 110), subtitle_text, fill=self.accent_color, font=subtitle_font)
            
            # Count text
            count_font = self._get_font(35, bold=False)
            count_text = f"I watched {len(monthly_entries)} movies."
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_x = (self.width - count_width) // 2
            draw.text((count_x, 170), count_text, fill=self.text_color, font=count_font)
            
        except Exception as e:
            print(f"Error drawing text: {e}")
        
        # Draw footer with Letterboxd branding
        try:
            # Heart icon (keep it classic)
            heart_size = 35
            heart_x = (self.width - heart_size) // 2
            heart_y = self.height - 100
            self._draw_heart_icon(draw, heart_x, heart_y, heart_size)
            
            # Add "for film lovers" text in Letterboxd style
            footer_font = self._get_font(24, bold=False)
            footer_text = "for film lovers"
            footer_bbox = draw.textbbox((0, 0), footer_text, font=footer_font)
            footer_width = footer_bbox[2] - footer_bbox[0]
            footer_x = (self.width - footer_width) // 2
            draw.text((footer_x, self.height - 50), footer_text, fill=self.text_color, font=footer_font)
            
        except Exception as e:
            print(f"Error drawing footer: {e}")
        
        print("Letterboxd Wrapped image created successfully!")
        return img