import requests
from bs4 import BeautifulSoup
import datetime
import json
import os

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_IMG_BASE_URL = 'https://image.tmdb.org/t/p/w154'
LB_BASE_URL = "https://letterboxd.com"


def get_movie_poster_url(title: str, year: str | int = "") -> str:
    """Returns the URL for the movie's poster"""

    """If (title, year) is not in databse, do an api request to
    TMDB to fetch url, then store in database the (title, year, url).
    Otherwise, just fetch from DB."""

    if (title, year) in ["database"]:
        # fetch from databse
        raise NotImplementedError("")
    else:
        response = requests.get(
            f"https://api.themoviedb.org/3/search/movie?query={title}&include_adult=false&language=en-US&page=1&year={year}&api_key={TMDB_API_KEY}",
            headers={"accept": "application/json"}
        )
        # TODO: store in DB

    return (
        TMDB_IMG_BASE_URL +
        json.loads(response.text)["results"][0]["poster_path"]
    )


def get_user_diary_entries(username: str, page: int) -> list[dict]:
    '''Returns the diary entries
    in letterboxd.com/<username>/films/diary/<page>'''

    url = f"{LB_BASE_URL}/{username}/films/diary/page/{page}"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    # Movie info (title, year & poster url)
    movie_titles = [i.text for i in soup.find_all("h3", class_="headline-3")]

    movie_release_years = [
        i.text
        for i in soup.find_all("td", class_="td-released")
    ]

    movie_poster_urls = [
        get_movie_poster_url(m, y)
        for m, y in list(zip(movie_titles, movie_release_years))
    ]

    diary_entry_months = []
    for i in soup.find_all("td", class_="td-calendar"):
        current_month = i.text if i.text != " " else current_month
        diary_entry_months.append(current_month.strip())

    diary_entry_days = [
        i.text.strip()
        for i in soup.find_all("td", class_="td-day")
    ]

    diary_entry_dates = [
        " ".join(d)
        for d in list(zip(diary_entry_days, diary_entry_months))
    ]

    diary_entry_dates = [
        datetime.datetime.strptime(d, "%d %b %Y")
        for d in diary_entry_dates
    ]

    return [
        {
            "diary_entry_date": diary_entry_dates[i],
            "movie_title": movie_titles[i],
            "movie_release_year": movie_release_years[i],
            "movie_poster_url": movie_poster_urls[i]
        }
        for i in range(len(movie_titles))
    ]


def get_last_n_days_of_movies_in_diary(username: str, n: int) -> list[dict]:
    '''Returns the diary entries from "letterboxd.com/<username>/films/diary"
    that is within "n" days from current day.'''
    diary_entries = get_user_diary_entries(username, 1)
    today = datetime.datetime.now()
    cutoff = (today - datetime.timedelta(n))
    c = 0
    for entry in diary_entries:
        if entry["diary_entry_date"] < cutoff:
            break
        c += 1
    return diary_entries[:c]