# letterboxd_scraper/wrapped.py - Enhanced with rounded corners, stats, and optional ratings
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
    def __init__(self, user, month=None, year=None, show_ratings=False):
        self.user = user
        self.month = month or datetime.now().month
        self.year = year or datetime.now().year
        self.month_name = month_name[self.month]
        self.show_ratings = show_ratings
        
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
        """Calculate interesting stats from diary entries"""
        stats = {
            'total_movies': len(entries),
            'liked_movies': 0,
            'rewatches': 0,
            'average_rating': 0,
            'top_rated_movies': [],
            'ratings_distribution': {}
        }
        
        ratings = []
        for entry in entries:
            # Count likes
            if entry.like:
                stats['liked_movies'] += 1
            
            # Count rewatches
            if entry.rewatch:
                stats['rewatches'] += 1
            
            # Process ratings
            if entry.rating and entry.rating.strip():
                # Convert star rating to number (★★★★★ = 5.0, ★★★★½ = 4.5, etc.)
                rating_str = entry.rating.strip()
                full_stars = rating_str.count('★')
                half_stars = rating_str.count('½')
                rating_value = full_stars + (half_stars * 0.5)
                
                if rating_value > 0:
                    ratings.append(rating_value)
                    
                    # Track high-rated movies (4+ stars)
                    if rating_value >= 4.0:
                        stats['top_rated_movies'].append({
                            'title': entry.film_title,
                            'rating': rating_value
                        })
        
        # Calculate average rating
        if ratings:
            stats['average_rating'] = sum(ratings) / len(ratings)
            
            # Count ratings distribution
            for rating in ratings:
                rating_key = f"{rating:.1f}"
                stats['ratings_distribution'][rating_key] = stats['ratings_distribution'].get(rating_key, 0) + 1
        
        # Sort top rated movies
        stats['top_rated_movies'].sort(key=lambda x: x['rating'], reverse=True)
        
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

    def _draw_stars_on_poster(self, poster_image, rating_str, width, height):
        """Draw star rating overlay on bottom of poster"""
        if not rating_str or not rating_str.strip():
            return poster_image
        
        try:
            # Create a copy of the poster to draw on
            poster_with_rating = poster_image.copy()
            draw = ImageDraw.Draw(poster_with_rating)
            
            # Create semi-transparent background for rating
            overlay_height = 30
            overlay_y = height - overlay_height
            
            # Draw dark overlay background
            overlay_coords = [0, overlay_y, width, height]
            draw.rectangle(overlay_coords, fill=(0, 0, 0, 180))
            
            # Draw stars
            star_font_size = min(16, width // 8)  # Adjust star size based on poster width
            try:
                star_font = self._get_font(star_font_size, bold=True)
            except:
                star_font = ImageFont.load_default()
            
            # Center the rating text
            rating_text = rating_str.strip()
            bbox = draw.textbbox((0, 0), rating_text, font=star_font)
            text_width = bbox[2] - bbox[0]
            text_x = (width - text_width) // 2
            text_y = overlay_y + (overlay_height - (bbox[3] - bbox[1])) // 2
            
            # Draw the stars in orange
            draw.text((text_x, text_y), rating_text, fill=self.accent_color, font=star_font)
            
            return poster_with_rating
            
        except Exception as e:
            print(f"Error adding stars to poster: {e}")
            return poster_image

    def _create_professional_grid(self, images, entries, max_posters=20):
        """Create a clean, professional grid layout"""
        layout_positions = []
        
        # Limit number of posters for clean design
        num_posters = min(len(images), max_posters)
        
        # Professional spacing and margins with more room for stats
        header_height = 380  # More room for title and stats
        footer_height = 180  # Room for count and hearts
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
        
        # Create grid positions with associated entry data
        for i in range(num_posters):
            row = i // best_config['cols']
            col = i % best_config['cols']
            
            x = side_margin + col * (best_config['poster_width'] + poster_spacing)
            y = start_y + row * (best_config['poster_height'] + poster_spacing)
            
            layout_positions.append({
                'x': int(x),
                'y': int(y),
                'width': int(best_config['poster_width']),
                'height': int(best_config['poster_height']),
                'entry': entries[i] if i < len(entries) else None
            })
        
        print(f"Created professional grid: {best_config['cols']}x{best_config['rows']} with {num_posters} posters")
        return layout_positions

    def _resize_image_clean(self, image, width, height):
        """Resize image with high quality"""
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

    def _draw_stats_section(self, draw, stats, y_position):
        """Draw a beautiful stats section"""
        try:
            stats_font = self._get_font(22, bold=False)
            stats_bold_font = self._get_font(24, bold=True)
            
            current_y = y_position
            line_height = 32
            center_x = self.width // 2
            
            # Create stats text
            stats_to_show = []
            
            if stats['average_rating'] > 0:
                stats_to_show.append(f"★ {stats['average_rating']:.1f} average rating")
            
            if stats['liked_movies'] > 0:
                stats_to_show.append(f"♥ {stats['liked_movies']} movies loved")
            
            if stats['rewatches'] > 0:
                stats_to_show.append(f"↻ {stats['rewatches']} rewatches")
            
            # Draw stats with different colors
            colors = [self.accent_color, "#FF6B6B", self.blue_color]
            
            for i, stat_text in enumerate(stats_to_show[:3]):  # Max 3 stats
                color = colors[i % len(colors)]
                
                # Calculate position for centered text
                bbox = draw.textbbox((0, 0), stat_text, font=stats_font)
                text_width = bbox[2] - bbox[0]
                text_x = center_x - text_width // 2
                
                draw.text((text_x, current_y), stat_text, fill=color, font=stats_font)
                current_y += line_height
            
            return current_y
            
        except Exception as e:
            print(f"Error drawing stats: {e}")
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
        
        # Draw movie posters with rounded corners and optional ratings
        for i, pos in enumerate(layout_positions):
            if i >= len(poster_images):
                break
                
            try:
                image = poster_images[i]
                entry = pos.get('entry')
                
                # Resize poster
                processed_poster = self._resize_image_clean(
                    image, pos['width'], pos['height']
                )
                
                # Add star ratings if enabled
                if self.show_ratings and entry and entry.rating:
                    processed_poster = self._draw_stars_on_poster(
                        processed_poster, entry.rating, pos['width'], pos['height']
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
        
        # Enhanced header with better spacing
        try:
            top_padding = 80
            
            # Main title
            title_font = self._get_font(44, bold=True)
            title_text = "month in movies"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_height = title_bbox[3] - title_bbox[1]
            title_x = (self.width - title_width) // 2
            title_y = top_padding + 20
            draw.text((title_x, title_y), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle with accent color
            subtitle_font = self._get_font(32, bold=True)
            subtitle_text = f"{self.month_name.upper()} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            subtitle_y = title_y + title_height + 20
            draw.text((subtitle_x, subtitle_y), subtitle_text, fill=self.accent_color, font=subtitle_font)
            
            # Draw stats section
            stats_y = subtitle_y + 45
            final_stats_y = self._draw_stats_section(draw, stats, stats_y)
            
        except Exception as e:
            print(f"Error drawing header: {e}")
        
        # Enhanced footer
        try:
            bottom_padding = 70
            
            # Movie count
            count_font = self._get_font(28, bold=False)
            count_text = f"I watched {len(monthly_entries)} movies."
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_height = count_bbox[3] - count_bbox[1]
            count_x = (self.width - count_width) // 2
            count_y = self.height - bottom_padding - count_height
            draw.text((count_x, count_y), count_text, fill=self.text_color, font=count_font)
            
            # Enhanced hearts with proper Letterboxd colors
            heart_size = 22
            heart_spacing = 18
            total_hearts_width = (3 * heart_size) + (2 * heart_spacing)
            
            hearts_start_x = (self.width - total_hearts_width) // 2
            hearts_y = count_y - heart_size - 30
            
            # Proper Letterboxd brand colors
            heart_colors = [
                self.accent_color,  # Orange
                self.green_color,   # Green  
                self.blue_color     # Blue
            ]
            
            for i in range(3):
                heart_x = hearts_start_x + i * (heart_size + heart_spacing)
                self._draw_heart_icon(draw, heart_x, hearts_y, heart_size, heart_colors[i])
            
        except Exception as e:
            print(f"Error drawing footer: {e}")
        
        print("Enhanced Letterboxd Wrapped image created successfully!")
        return img