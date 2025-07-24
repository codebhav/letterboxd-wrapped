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
        """Create a dense, overlapping layout like the NYT reference"""
        layout_positions = []
        
        # Larger base poster sizes for better visibility
        base_width = 180
        base_height = int(base_width * 1.5)  # Movie poster aspect ratio
        
        # Define zones for placement (avoiding header and footer areas)
        header_height = 350
        footer_height = 150
        available_height = self.height - header_height - footer_height
        available_width = self.width - 60  # 30px margin on each side
        
        # Create overlapping clusters for more dynamic feel
        # Use more posters to fill the space better
        num_posters = min(len(images), 25)
        
        # Define several "focus areas" where posters will cluster (more strategic placement)
        focus_areas = [
            # Main central cluster
            {'x': available_width * 0.5, 'y': header_height + available_height * 0.4, 'weight': 2.0},
            # Upper left
            {'x': available_width * 0.25, 'y': header_height + available_height * 0.2, 'weight': 1.5},
            # Upper right  
            {'x': available_width * 0.75, 'y': header_height + available_height * 0.25, 'weight': 1.3},
            # Lower left
            {'x': available_width * 0.2, 'y': header_height + available_height * 0.75, 'weight': 1.2},
            # Lower right
            {'x': available_width * 0.8, 'y': header_height + available_height * 0.7, 'weight': 1.1},
            # Middle left
            {'x': available_width * 0.15, 'y': header_height + available_height * 0.5, 'weight': 0.8},
            # Middle right
            {'x': available_width * 0.85, 'y': header_height + available_height * 0.45, 'weight': 0.9},
            # Fill gaps
            {'x': available_width * 0.6, 'y': header_height + available_height * 0.15, 'weight': 0.7},
            {'x': available_width * 0.4, 'y': header_height + available_height * 0.8, 'weight': 0.6},
        ]
        
        for i in range(num_posters):
            # Choose a focus area (higher weight = more likely to be chosen)
            weights = [area['weight'] for area in focus_areas]
            chosen_area = random.choices(focus_areas, weights=weights)[0]
            
            # Size variation - some bigger, some smaller for hierarchy
            if i < 3:  # First few posters are larger
                size_multiplier = random.uniform(1.2, 1.6)
            elif i < 8:  # Medium group
                size_multiplier = random.uniform(0.9, 1.3)
            else:  # Smaller background posters
                size_multiplier = random.uniform(0.7, 1.1)
                
            poster_width = int(base_width * size_multiplier)
            poster_height = int(base_height * size_multiplier)
            
            # Position near the chosen focus area with some randomness  
            spread = 120 if i < 10 else 160  # Tighter clustering for main posters
            x = chosen_area['x'] + random.randint(-spread, spread)
            y = chosen_area['y'] + random.randint(-spread//2, spread//2)
            
            # Ensure poster fits within bounds (with overlap allowed)
            margin = 30
            if x < -poster_width//2:  # Allow partial off-screen on sides
                x = -poster_width//2
            if x > self.width - poster_width//2:
                x = self.width - poster_width//2
            if y < header_height:
                y = header_height + random.randint(0, 50)
            if y + poster_height > self.height - footer_height:
                y = self.height - footer_height - poster_height + random.randint(-30, 0)
            
            # More subtle rotation for cleaner look
            rotation = random.randint(-12, 12)
            
            # Z-index for layering (earlier posters go on top)
            z_index = num_posters - i
            
            layout_positions.append({
                'x': int(x),
                'y': int(y), 
                'width': poster_width,
                'height': poster_height,
                'rotation': rotation,
                'z_index': z_index
            })
        
        # Sort by z_index so we draw background posters first
        layout_positions.sort(key=lambda pos: pos['z_index'])
        
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
        
        # Get poster images (use more for denser layout)
        num_posters = min(25, len(monthly_entries))
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
        
        # Draw movie posters with proper layering
        temp_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        
        for i, pos in enumerate(layout_positions):
            if i >= len(poster_images):
                break
                
            try:
                image = poster_images[i]
                
                # Resize and rotate poster
                processed_poster = self._resize_and_rotate_image(
                    image, pos['width'], pos['height'], pos['rotation']
                )
                
                # Calculate position for rotated image
                paste_x = pos['x'] - (processed_poster.width - pos['width']) // 2
                paste_y = pos['y'] - (processed_poster.height - pos['height']) // 2
                
                # Create a layer for this poster with shadow
                poster_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                
                # Add drop shadow
                shadow_offset = 2
                shadow_img = Image.new('RGBA', processed_poster.size, (0, 0, 0, 30))
                if paste_x + shadow_offset + processed_poster.width <= self.width and \
                   paste_y + shadow_offset + processed_poster.height <= self.height and \
                   paste_x + shadow_offset >= 0 and paste_y + shadow_offset >= 0:
                    poster_layer.paste(shadow_img, (paste_x + shadow_offset, paste_y + shadow_offset), shadow_img)
                
                # Paste the poster
                if paste_x + processed_poster.width <= self.width and \
                   paste_y + processed_poster.height <= self.height and \
                   paste_x >= -processed_poster.width//2 and paste_y >= 0:  # Allow partial off-screen
                    
                    if processed_poster.mode == 'RGBA':
                        poster_layer.paste(processed_poster, (paste_x, paste_y), processed_poster)
                    else:
                        poster_layer.paste(processed_poster, (paste_x, paste_y))
                
                # Composite this layer onto temp_img
                temp_img = Image.alpha_composite(temp_img, poster_layer)
                    
            except Exception as e:
                print(f"Error placing poster {i}: {e}")
                continue
        
        # Composite the posters onto the background
        img = Image.alpha_composite(img.convert('RGBA'), temp_img).convert('RGB')
        draw = ImageDraw.Draw(img)
        
        # Draw header text (more compact to give more space to posters)
        try:
            # Main title
            title_font = self._get_font(45, bold=True)
            title_text = "LETTERBOXD WRAPPED"
            title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (self.width - title_width) // 2
            draw.text((title_x, 60), title_text, fill=self.text_color, font=title_font)
            
            # Subtitle
            subtitle_font = self._get_font(50, bold=True)
            subtitle_text = f"{self.month_name.upper()} {self.year}"
            subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.width - subtitle_width) // 2
            draw.text((subtitle_x, 120), subtitle_text, fill=self.text_color, font=subtitle_font)
            
            # Count text
            count_font = self._get_font(35, bold=False)
            count_text = f"I watched {len(monthly_entries)} movies."
            count_bbox = draw.textbbox((0, 0), count_text, font=count_font)
            count_width = count_bbox[2] - count_bbox[0]
            count_x = (self.width - count_width) // 2
            draw.text((count_x, 180), count_text, fill=self.text_color, font=count_font)
            
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

# ====================================
# letterboxd_scraper/__init__.py (Updated)
from .letterboxd_user import LetterboxdUser
from .collage import Collage
from .wrapped import LetterboxdWrapped

# ====================================
# wrapped_generator.py (New main script)
import argparse
import os
from datetime import datetime
from calendar import month_name
from letterboxd_scraper import LetterboxdUser, LetterboxdWrapped

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Letterboxd Wrapped images for Instagram Stories"
    )
    parser.add_argument(
        "username",
        help="Letterboxd username"
    )
    parser.add_argument(
        "--month", "-m",
        help="Month (1-12)",
        type=int,
        default=datetime.now().month
    )
    parser.add_argument(
        "--year", "-y", 
        help="Year",
        type=int,
        default=datetime.now().year  # Back to current year
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory",
        default="./wrapped_output"
    )
    
    args = parser.parse_args()
    
    # Validate month
    if args.month < 1 or args.month > 12:
        print("Month must be between 1 and 12")
        exit(1)
    
    # Create output directory
    if not os.path.isdir(args.output):
        os.makedirs(args.output)
    
    try:
        # Create user and wrapped generator
        user = LetterboxdUser(args.username)
        wrapped = LetterboxdWrapped(user, month=args.month, year=args.year)
        
        # Generate wrapped image
        image = wrapped.create()
        
        # Save image
        month_name_str = month_name[args.month]
        filename = f"{args.username}_wrapped_{month_name_str}_{args.year}.jpg"
        filepath = os.path.join(args.output, filename)
        
        image.save(filepath, "JPEG", quality=95)
        print(f"\nWrapped image saved: {filepath}")
        
    except Exception as e:
        print(f"Error creating wrapped image: {e}")
        exit(1)

# ====================================
# app/wrapped_server.py (New Flask app for wrapped)
from io import BytesIO
import traceback
from datetime import datetime
from calendar import month_name

from flask import (
    Flask,
    flash,
    redirect,
    request,
    render_template,
    send_file,
    url_for,
    jsonify
)

from letterboxd_scraper import LetterboxdUser, LetterboxdWrapped

app = Flask(__name__)
app.secret_key = "letterboxd-wrapped-secret-key"

@app.route("/", methods=["GET", "POST"])
def index():
    current_month = datetime.now().month
    current_year = datetime.now().year  # Back to current year
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if not username:
            flash("Please enter a username")
            months = [(i, month_name[i]) for i in range(1, 13)]
            years = list(range(current_year, current_year - 5, -1))
            return render_template("wrapped_index.html", 
                                 months=months, 
                                 years=years,
                                 current_month=current_month,
                                 current_year=current_year)
        
        month = int(request.form.get("month", current_month))
        year = int(request.form.get("year", current_year))
            
        return redirect(
            url_for(
                "wrapped",
                username=username,
                month=month,
                year=year
        ))
    
    # Prepare month options for the form
    months = [(i, month_name[i]) for i in range(1, 13)]
    years = list(range(current_year, current_year - 5, -1))  # Current year to 5 years back
    
    return render_template("wrapped_index.html", 
                         months=months, 
                         years=years,
                         current_month=current_month,
                         current_year=current_year)

@app.route("/wrapped")
def wrapped():
    username = request.args.get("username", "").strip()
    month = int(request.args.get("month", datetime.now().month))
    year = int(request.args.get("year", datetime.now().year))
    
    if username:
        return render_template(
            "wrapped_result.html",
            username=username,
            month=month,
            year=year,
            month_name=month_name[month]
        )
    
    flash("Username not provided.")
    return redirect(url_for("index"))

@app.route("/wrapped-img")
def wrapped_img():
    username = request.args.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400
        
    try:
        month = int(request.args.get("month", datetime.now().month))
        year = int(request.args.get("year", datetime.now().year))
        
        wrapped_io = create_wrapped_image(username, month, year)
        return send_file(
            wrapped_io,
            mimetype="image/jpeg",
            as_attachment=False
        )
    except Exception as e:
        print(f"Error creating wrapped image: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def create_wrapped_image(username, month, year):
    wrapped_io = BytesIO()
    
    try:
        user = LetterboxdUser(username)
        wrapped = LetterboxdWrapped(user, month=month, year=year)
        wrapped_image = wrapped.create()
        wrapped_image.save(wrapped_io, format="JPEG", quality=95)
        wrapped_io.seek(0)
        return wrapped_io
    except Exception as e:
        print(f"Error in create_wrapped_image: {e}")
        raise

if __name__ == "__main__":
    app.run(debug=True)