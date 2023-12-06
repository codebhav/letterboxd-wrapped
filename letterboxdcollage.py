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
    parser.add_argument(
        "--hide-shorts", "-hs",
        help="Exclude short films from collage",
        action="store_true"
    )
    parser.add_argument(
        "--hide-tv", "-ht",
        help="Exclude TV shows from collage",
        action="store_true"
    )
    parser.add_argument(
        "--hide-docs", "-hd",
        help="Exclude documentaries from collage",
        action="store_true"
    )
    parser.add_argument(
        "--only-films", "-of",
        help="Only include films in collage (exclude short films, TV shows, and documentaries)",
        action="store_true"
    )
    args = parser.parse_args()
    WIDTH, HEIGHT = (5, 5)
    diary_filters = {
        "only-films": args.only_films,
        "hide-shorts": args.hide_shorts,
        "hide-tv": args.hide_tv,
        "hide-docs": args.hide_docs
    }
    if args.size:
        WIDTH, HEIGHT = args.size
        if WIDTH * HEIGHT > 50:
            print("Invalid arguments to --size WIDTH HEIGHT")
            print("WIDTH * HEIGHT must be 50 or less")
            exit()
    Collage(LetterboxdUser(args.username, diary_filters=diary_filters)) \
        .create(size=(WIDTH, HEIGHT)) \
        .save(f"{args.username}_collage_{WIDTH}x{HEIGHT}.jpg")
