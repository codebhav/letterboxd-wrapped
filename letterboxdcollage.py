import argparse
from letterboxd_scraper import LetterboxdUser, Collage

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Make collages from your Letterboxd diary"\
    )
    parser.add_argument(
        "username",
        help="Letterboxd username"
    )
    parser.add_argument(
        "--size", "-s",
        help="Collage size (WIDTH, HEIGHT). WIDTH * HEIGHT must be 50 or less",
        nargs=2,
        type=int,
    )
    args = parser.parse_args()
    WIDTH, HEIGHT = (5, 5)
    if args.size:
        WIDTH, HEIGHT = args.size
        if WIDTH * HEIGHT > 50:
            print("Invalid arguments to --size WIDTH HEIGHT")
            print("WIDTH * HEIGHT must be 50 or less")
            exit()
    Collage(LetterboxdUser(args.username)) \
        .create(size=(WIDTH, HEIGHT)) \
        .save(f"{args.username}_collage_{WIDTH}x{HEIGHT}.jpg")
