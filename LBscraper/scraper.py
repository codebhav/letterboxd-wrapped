import requests
from bs4 import BeautifulSoup
import datetime


def get_movie_poster_url(slug: str, k: str = "") -> str:
    print(f"Getting movie poster url for: {slug, k} ...")
    res = requests.get(f"https://letterboxd.com/ajax/poster/film/{slug}/std/230x345/?k={k}")
    soup = BeautifulSoup(res.text, "html.parser")
    return soup.find("img", class_="image")["src"]


def get_user_diary_entries(username: str, page: int) -> list[dict]:
    '''Returns the diary entries
    in letterboxd.com/<username>/films/diary/<page>'''

    url = f"https://letterboxd.com/{username}/films/diary/page/{page}"
    res = requests.get(url)

    if not res.ok:
        """Username does not exist"""
        return []

    soup = BeautifulSoup(res.text, "html.parser")

    movie_slug_and_cache_key = [
        (i["data-film-slug"], i["data-cache-busting-key"])
        for i in soup.find_all("div", class_="film-poster")
    ]

    movie_poster_urls = [
        get_movie_poster_url(slug, k)
        for slug, k in movie_slug_and_cache_key
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
        for d in zip(diary_entry_days, diary_entry_months)
    ]

    diary_entry_dates = [
        datetime.datetime.strptime(d, "%d %b %Y")
        for d in diary_entry_dates
    ]

    return [
        {
            "diary_entry_date": diary_entry_dates[i],
            "movie_slug": movie_slug_and_cache_key[i][0],
            "movie_poster_url": movie_poster_urls[i]
        }
        for i in range(len(movie_poster_urls))
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