# letterboxd_scraper/wrapped.py - Professional Apple-style redesign with proper padding
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

    def _create_professional_grid(self, images, max_posters=25):
        """Create a clean, professional grid layout like NYT/Apple design"""
        layout_positions = []
        
        # Limit number of posters for clean design
        num_posters = min(len(images), max_posters)
        
        # UPDATED: Professional spacing and margins with better padding
        header_height = 320  # Increased to accommodate pushed down header text
        footer_height = 160  # Adjusted for simpler footer without "for film lovers"
        side_margin = 60     # Generous side margins
        poster_spacing = 20  # Clean spacing between posters
        
        # Calculate available space
        available_height = self.height - header_height - footer_height
        available_width = self.width - (2 * side_margin)
        
        # Determine optimal grid configuration
        # Prioritize clean rectangular grids
        best_config = None
        best_score = 0
        
        # Try common grid ratios that look professional
        for cols in range(3, 7):  # 3-6 columns work best for mobile
            rows = math.ceil(num_posters / cols)
            
            # Calculate poster dimensions
            poster_width = (available_width - (cols - 1) * poster_spacing) / cols
            poster_height = poster_width * 1.5  # Standard movie poster ratio
            
            # Calculate total grid height
            total_grid_height = rows * poster_height + (rows - 1) * poster_spacing
            
            # Check if it fits and calculate quality score
            if total_grid_height <= available_height:
                # Score based on poster size and how well it uses space
                space_efficiency = total_grid_height / available_height
                poster_size_score = poster_width / 200  # Prefer larger posters
                
                # Bonus for common grid ratios (4x4, 5x5, etc.)
                ratio_bonus = 1.2 if cols == rows else 1.0
                
                score = poster_size_score * space_efficiency * ratio_bonus
                
                if score > best_score:
                    best_score = score
                    best_config = {
                        'cols': cols,
                        'rows': rows,
                        'poster_width': poster_width,
                        'poster_height': poster_height,
                        'total_grid_height': total_grid_height
                    }
        
        if not best_config:
            # Fallback configuration
            best_config = {
                'cols': 4,
                'rows': math.ceil(num_posters / 4),
                'poster_width': 180,
                'poster_height': 270,
                'total_grid_height': math.ceil(num_posters / 4) * 270 + (math.ceil(num_posters / 4) - 1) * poster_spacing
            }
        
        # Center the grid vertically in available space
        vertical_margin = (available_height - best_config['total_grid_height']) / 2
        start_y = header_height + vertical_margin
        
        # Create perfectly aligned grid positions
        for i in range(num_posters):
            row = i // best_config['cols']
            col = i % best_config['cols']
            
            # Calculate exact position (no randomness for professional look)
            x = side_margin + col * (best_config['poster_width'] + poster_spacing)
            y = start_y + row * (best_config['poster_height'] + poster_spacing)
            
            layout_positions.append({
                'x': int(x),
                'y': int(y),
                'width': int(best_config['poster_width']),
                'height': int(best_config['poster_height']),
                'rotation': 0,  # No rotation for clean professional look
                'z_index': i
            })
        
        print(f"Created professional grid: {best_config['cols']}x{best_config['rows']} with {num_posters} posters")
        return layout_positions

    def _resize_image_clean(self, image, width, height):
        """Resize image with high quality, no rotation"""
        return image.resize((width, height), Image.Resampling.LANCZOS)

    def _draw_heart_icon(self, draw, x, y, size=24, color=None):
        """Draw a clean heart icon with specified color"""
        heart_color = color or self.accent_color
        
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
        """Create the Instagram Story wrapped image with professional design"""
        print(f"Creating Letterboxd Wrapped for {self.month_name} {self.year}...")
        
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
        
        # Create professional grid layout
        layout_positions = self._create_professional_grid(poster_images)
        
        # Draw movie posters with clean shadows
        for i, pos in enumerate(layout_positions):
            if i >= len(poster_images):
                break
                
            try:
                image = poster_images[i]
                
                # Resize poster (no rotation for clean look)
                processed_poster = self._resize_image_clean(
                    image, pos['width'], pos['height']
                )
                
                # Add professional drop shadow (simplified for reliability)
                shadow_offset = 3
                shadow_color = (20, 20, 20)  # Dark gray shadow
                
                # Create simple shadow
                shadow_x = pos['x'] + shadow_offset
                shadow_y = pos['y'] + shadow_offset
                
                # Draw shadow rectangle directly on main image
                temp_draw = ImageDraw.Draw(img)
                temp_draw.rectangle(
                    [shadow_x, shadow_y, 
                     shadow_x + pos['width'], shadow_y + pos['height']],
                    fill=shadow_color
                )
                
                # Paste the poster on top
                img.paste(processed_poster, (pos['x'], pos['y']))
                    
            except Exception as e:
                print(f"Error placing poster {i}: {e}")
                continue
        
        # Redraw for text
        draw = ImageDraw.Draw(img)
        
        # UPDATED: Professional typography with proper padding and spacing
        try:
            # Professional padding from edges - pushed further down
            top_padding = 100  # More generous top padding
            
            # Main title - clean and prominent with proper spacing
            title_font = self._get_font(42, bold=True)
            title_text = "LETTERBOXD WRAPPED"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = top_padding + 40  # Pushed further down from top
            draw.text((title_x, title_y), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle with accent color and proper spacing below title
            subtitle_font = self._get_font(36, bold=True)
            subtitle_text = f"{self.month_name.upper()} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 25  # Better spacing below title
            draw.text((subtitle_x, subtitle_y), subtitle_text, fill=self.accent_color, font=subtitle_font)
            
        except Exception as e:
            print(f"Error drawing header text: {e}")
        
        # UPDATED: Clean footer design with proper padding from bottom
        try:
            # Professional padding from bottom
            bottom_padding = 80  # Generous bottom padding
            
            # Movie count - positioned at bottom with good spacing
            count_font = self._get_font(28, bold=False)
            count_text = f"I watched {len(monthly_entries)} movies."
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_height = count_bbox[3] - count_bbox[1]
            count_x = (self.width - count_width) // 2
            count_y = self.height - bottom_padding - count_height
            draw.text((count_x, count_y), count_text, fill=self.text_color, font=count_font)
            
            # Three hearts with Letterboxd colors - positioned above movie count
            heart_size = 20
            heart_spacing = 15  # Space between hearts
            total_hearts_width = (3 * heart_size) + (2 * heart_spacing)
            
            # Center the group of hearts
            hearts_start_x = (self.width - total_hearts_width) // 2
            hearts_y = count_y - heart_size - 25  # 25px spacing above movie count
            
            # Letterboxd color palette for hearts
            heart_colors = [
                "#FF8000",  # Letterboxd orange
                "#FFFFFF",  # White  
                "#CCCCCC"   # Light gray
            ]
            
            # Draw three hearts
            for i in range(3):
                heart_x = hearts_start_x + i * (heart_size + heart_spacing)
                self._draw_heart_icon(draw, heart_x, hearts_y, heart_size, heart_colors[i])
            
        except Exception as e:
            print(f"Error drawing footer: {e}")
        
        print("Professional Letterboxd Wrapped image created successfully!")
        return img