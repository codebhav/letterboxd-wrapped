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
