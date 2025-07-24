# letterboxd_scraper/wrapped.py - Enhanced with clean emoji stats like reference
import random
import math
from datetime import datetime, timedelta
from calendar import month_name
import platform
from pathlib import Path
from collections import Counter

from PIL import Image, ImageDraw, ImageFont, ImageOps
import requests

from .config import IMG_DIM

class LetterboxdWrapped:
    def __init__(self, user, month=None, year=None):
        self.user = user
        self.month = month or datetime.now().month
        self.year = year or datetime.now().year
        self.month_name = month_name[self.month].lower()
        
        # Instagram Story dimensions
        self.width = 1080
        self.height = 1920
        
        # Enhanced Letterboxd brand colors
        self.bg_color = "#14181C"  # Letterboxd's dark blue-gray background
        self.text_color = "#FFFFFF"  # White text
        self.accent_color = "#FF8000"  # Letterboxd's signature orange
        self.green_color = "#00D15B"   # Letterboxd green
        self.blue_color = "#00A2F5"    # Letterboxd blue
        self.secondary_text = "#B8C5D1"  # Light gray for secondary text
        
    def _get_font(self, size=40, bold=False):
        """Get Helvetica font based on operating system"""
        try:
            system = platform.system()
            if system == "Windows":
                # Try Helvetica first, then Arial as fallback
                font_paths = [
                    "HelveticaNeue.ttf" if not bold else "HelveticaNeue-Bold.ttf",
                    "helvetica.ttf" if not bold else "helveticab.ttf", 
                    "arial.ttf" if not bold else "arialbd.ttf"
                ]
                for font_path in font_paths:
                    try:
                        return ImageFont.truetype(font_path, size=size)
                    except:
                        continue
                        
            elif system == "Darwin":  # macOS
                font_paths = [
                    "/System/Library/Fonts/Helvetica.ttc",
                    "/System/Library/Fonts/HelveticaNeue.ttc",
                    "/System/Library/Fonts/Arial.ttf"
                ]
                for font_path in font_paths:
                    if Path(font_path).exists():
                        return ImageFont.truetype(font_path, size=size)
                        
            else:  # Linux
                font_paths = [
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/TTF/DejaVuSans.ttf"
                ]
                for font_path in font_paths:
                    if Path(font_path).exists():
                        return ImageFont.truetype(font_path, size=size)
                        
        except Exception as e:
            print(f"Font loading error: {e}")
        
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
                    
                    if entry_year == self.year and entry_month == self.month:
                        monthly_entries.append(entry)
            except (ValueError, IndexError) as e:
                print(f"Error parsing date '{entry.date}': {e}")
                continue
        
        print(f"Found {len(monthly_entries)} entries for {target_month_name} {self.year}")
        return monthly_entries

    def _calculate_stats(self, entries):
        """Calculate stats for the clean emoji layout"""
        stats = {
            'total_movies': len(entries),
            'liked_movies': 0,
            'average_rating': 0.0
        }
        
        ratings = []
        for entry in entries:
            # Count likes
            if entry.like:
                stats['liked_movies'] += 1
            
            # Process ratings
            if entry.rating and entry.rating.strip():
                # Convert star rating to number (★★★★★ = 5.0, ★★★★½ = 4.5, etc.)
                rating_str = entry.rating.strip()
                full_stars = rating_str.count('★')
                half_stars = rating_str.count('½')
                rating_value = full_stars + (half_stars * 0.5)
                
                if rating_value > 0:
                    ratings.append(rating_value)
        
        # Calculate average rating
        if ratings:
            stats['average_rating'] = sum(ratings) / len(ratings)
        
        return stats

    def _add_rounded_corners(self, image, radius=15):
        """Add rounded corners to an image"""
        # Create a mask with rounded corners
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([(0, 0), image.size], radius=radius, fill=255)
        
        # Apply the mask
        rounded_image = Image.new('RGBA', image.size, (0, 0, 0, 0))
        rounded_image.paste(image, (0, 0))
        rounded_image.putalpha(mask)
        
        return rounded_image

    def _create_professional_grid(self, images, entries, max_posters=20):
        """Create a clean, professional grid layout"""
        layout_positions = []
        
        # Limit number of posters for clean design
        num_posters = min(len(images), max_posters)
        
        # Professional spacing and margins with room for stats
        header_height = 350  # Reduced since stats are now horizontal 
        footer_height = 80   # Minimal footer
        side_margin = 60     
        poster_spacing = 15  # Tighter spacing for more posters
        
        # Calculate available space
        available_height = self.height - header_height - footer_height
        available_width = self.width - (2 * side_margin)
        
        # Determine optimal grid configuration
        best_config = None
        best_score = 0
        
        for cols in range(3, 7):  
            rows = math.ceil(num_posters / cols)
            
            # Calculate poster dimensions
            poster_width = (available_width - (cols - 1) * poster_spacing) / cols
            poster_height = poster_width * 1.5  # Standard movie poster ratio
            
            # Calculate total grid height
            total_grid_height = rows * poster_height + (rows - 1) * poster_spacing
            
            # Check if it fits and calculate quality score
            if total_grid_height <= available_height:
                space_efficiency = total_grid_height / available_height
                poster_size_score = poster_width / 200  
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
        
        # Create grid positions
        for i in range(num_posters):
            row = i // best_config['cols']
            col = i % best_config['cols']
            
            x = side_margin + col * (best_config['poster_width'] + poster_spacing)
            y = start_y + row * (best_config['poster_height'] + poster_spacing)
            
            layout_positions.append({
                'x': int(x),
                'y': int(y),
                'width': int(best_config['poster_width']),
                'height': int(best_config['poster_height'])
            })
        
        print(f"Created professional grid: {best_config['cols']}x{best_config['rows']} with {num_posters} posters")
        return layout_positions

    def _resize_image_clean(self, image, width, height):
        """Resize image with high quality"""
        return image.resize((width, height), Image.Resampling.LANCZOS)

    def _draw_emoji_stats(self, draw, stats, y_position):
        """Draw horizontal emoji stats layout matching reference"""
        try:
            # Use text symbols instead of emojis for better compatibility
            symbol_font = self._get_font(28, bold=True)  # For symbols  
            number_font = self._get_font(28, bold=True)  # For numbers
            
            center_x = self.width // 2
            
            # Stats data with text symbols (more reliable than emojis)
            stats_data = [
                ("👀", str(stats['total_movies'])),
                ("★", f"{stats['average_rating']:.1f}" if stats['average_rating'] > 0 else "0.0"),
                ("♥", str(stats['liked_movies']))
            ]
            
            # Calculate total width for all stats
            spacing_between_stats = 60  # Space between each stat group
            stat_widths = []
            
            for symbol, value in stats_data:
                # Calculate width of "symbol value" 
                symbol_bbox = draw.textbbox((0, 0), symbol, font=symbol_font)
                value_bbox = draw.textbbox((0, 0), value, font=number_font)
                
                symbol_width = symbol_bbox[2] - symbol_bbox[0]
                value_width = value_bbox[2] - value_bbox[0]
                
                stat_width = symbol_width + 12 + value_width  # 12px between symbol and number
                stat_widths.append(stat_width)
            
            # Total width of all stats
            total_width = sum(stat_widths) + (len(stats_data) - 1) * spacing_between_stats
            
            # Starting x position to center everything
            start_x = center_x - total_width // 2
            current_x = start_x
            
            # Colors for each stat
            colors = [self.text_color, self.accent_color, "#FF6B6B"]  # white, orange, red
            
            for i, (symbol, value) in enumerate(stats_data):
                color = colors[i % len(colors)]
                
                # Draw symbol
                draw.text((current_x, y_position), symbol, fill=color, font=symbol_font)
                
                # Calculate symbol width and draw number
                symbol_bbox = draw.textbbox((0, 0), symbol, font=symbol_font)
                symbol_width = symbol_bbox[2] - symbol_bbox[0]
                
                number_x = current_x + symbol_width + 12
                draw.text((number_x, y_position), value, fill=self.text_color, font=number_font)
                
                # Move to next stat position
                current_x += stat_widths[i] + spacing_between_stats
            
            return y_position + 40  # Return position after stats
            
        except Exception as e:
            print(f"Error drawing emoji stats: {e}")
            return y_position

    def create(self):
        """Create the enhanced Instagram Story wrapped image"""
        print(f"Creating Enhanced Letterboxd Wrapped for {self.month_name} {self.year}...")
        
        # Get monthly entries
        monthly_entries = self._get_monthly_diary_entries()
        
        if not monthly_entries:
            raise ValueError(f"No diary entries found for {self.month_name} {self.year}")
        
        print(f"Found {len(monthly_entries)} movies watched in {self.month_name} {self.year}")
        
        # Calculate stats
        stats = self._calculate_stats(monthly_entries)
        print(f"Stats: {stats['total_movies']} movies, {stats['liked_movies']} liked, avg rating: {stats['average_rating']:.1f}")
        
        # Create base image with gradient background
        img = Image.new('RGB', (self.width, self.height), self.bg_color)
        draw = ImageDraw.Draw(img)
        
        # Add subtle gradient background
        for y in range(self.height):
            gradient_factor = y / self.height
            r = int(20 + gradient_factor * 8)  # 20 -> 28
            g = int(24 + gradient_factor * 8)  # 24 -> 32  
            b = int(28 + gradient_factor * 8)  # 28 -> 36
            color = (r, g, b)
            draw.line([(0, y), (self.width, y)], fill=color)
        
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
        layout_positions = self._create_professional_grid(poster_images, monthly_entries)
        
        # Draw movie posters with rounded corners
        for i, pos in enumerate(layout_positions):
            if i >= len(poster_images):
                break
                
            try:
                image = poster_images[i]
                
                # Resize poster
                processed_poster = self._resize_image_clean(
                    image, pos['width'], pos['height']
                )
                
                # Add rounded corners
                rounded_poster = self._add_rounded_corners(processed_poster, radius=12)
                
                # Create shadow
                shadow_offset = 4
                shadow_color = (10, 10, 10, 100)  # Semi-transparent shadow
                
                # Draw shadow
                shadow = Image.new('RGBA', (pos['width'] + shadow_offset, pos['height'] + shadow_offset), (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.rounded_rectangle(
                    [(shadow_offset, shadow_offset), (pos['width'], pos['height'])],
                    radius=12, fill=shadow_color
                )
                
                # Paste shadow first, then poster
                img.paste(shadow, (pos['x'], pos['y']), shadow)
                img.paste(rounded_poster, (pos['x'], pos['y']), rounded_poster)
                    
            except Exception as e:
                print(f"Error placing poster {i}: {e}")
                continue
        
        # Redraw for text
        draw = ImageDraw.Draw(img)
        
        # Enhanced header with username
        try:
            top_padding = 80
            
            # Main title: "username's month in movies"
            title_font = self._get_font(38, bold=True)
            title_text = f"{self.user.username}'s month in movies"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = top_padding + 20
            draw.text((title_x, title_y), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle with accent color  
            subtitle_font = self._get_font(26, bold=True)
            subtitle_text = f"{self.month_name} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 15
            draw.text((subtitle_x, subtitle_y), subtitle_text, fill=self.accent_color, font=subtitle_font)
            
            # Draw clean emoji stats section (HORIZONTAL layout)
            stats_y = subtitle_y + 35
            final_stats_y = self._draw_emoji_stats(draw, stats, stats_y)
            
        except Exception as e:
            print(f"Error drawing header: {e}")
        
        print("Enhanced Letterboxd Wrapped image created successfully!")
        return img