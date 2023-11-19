import requests
from bs4 import BeautifulSoup

from .film import Film, DiaryEntry


class LetterboxdUser:
    def __init__(self, username: str):
        self.username = username
        self.profile_url = f"https://letterboxd.com/{self.username}"
        self._profile_name = None
        self._total_films = None
        self._total_films_this_year = None
        self._lists = None
        self._following = None
        self._followers = None
        self._pro = None
        self._bio = None
        self._diary = {}
        self._four_faves = None

    @property
    def profile_name(self):
        if self._profile_name is not None:
            return self._profile_name
        self.get_profile_info()
        return self._profile_name

    @property
    def total_films(self):
        if self._total_films is not None:
            return self._total_films
        self.get_profile_info()
        return self._total_films

    @property
    def total_films_this_year(self):
        if self._total_films_this_year is not None:
            return self._total_films_this_year
        self.get_profile_info()
        return self._total_films_this_year

    @property
    def lists(self):
        if self._lists is not None:
            return self._lists
        self.get_profile_info()
        return self._lists

    @property
    def following(self):
        if self._following is not None:
            return self._following
        self.get_profile_info()
        return self._following

    @property
    def followers(self):
        if self._followers is not None:
            return self._followers
        self.get_profile_info()
        return self._followers

    @property
    def pro(self):
        if self._pro is not None:
            return self._pro
        self.get_profile_info()
        return self._pro

    @property
    def bio(self):
        if self._bio is not None:
            return self._bio
        self.get_profile_info()
        return self._bio

    @property
    def four_faves(self):
        if self._four_faves is not None:
            return self._four_faves
        self.get_profile_info()
        return self._four_faves

    def get_profile_info(self):
        print("Fetching profile information...")
        res = requests.get(self.profile_url)
        soup = BeautifulSoup(res.text, "html.parser")
        profile_name = soup.find("div", class_="profile-name-wrap").h1.text
        profile_statistics = []
        for stat in soup.find_all("h4", "profile-statistic"):
            profile_statistics.append(
                int("".join([c for c in stat.text if c.isdigit()]))
            )
        if len(profile_statistics) == 4:
            profile_statistics.insert(2, 0)
        pro = soup.find("span", class_="badge")
        bio = soup.find("section", id="person-bio") or \
            soup.find("div", class_="bio")
        ffaves = []
        for f in soup.find_all("li", class_="favourite-film-poster-container"):
            ffaves.append(
                Film(
                    film_title=f.div.img["alt"],
                    film_year=None,
                    film_slug=f.div["data-film-slug"])
            )
        # TODO: include <a> links in bio text
        self._profile_name = profile_name
        self._total_films = profile_statistics[0]
        self._total_films_this_year = profile_statistics[1]
        self._lists = profile_statistics[2]
        self._following = profile_statistics[3]
        self._followers = profile_statistics[4]
        self._pro = True if pro else False
        self._bio = bio.div.get_text("\n", strip=True) if bio else ""
        self._four_faves = ffaves

    def diary(self, page=1) -> list[DiaryEntry] | None:
        if str(page) in self._diary:
            return self._diary[str(page)]

        print(f"Fetching diary entries on page {page}...")
        diary_entries = []
        res = requests.get(self.profile_url + f"/films/diary/page/{page}")
        soup = BeautifulSoup(res.text, "html.parser")
        rows = soup.find_all("tr", class_="diary-entry-row")

        if not rows:
            print(f"Diary page {page} does not exist")
            return

        current_year = rows[0].td.small.text
        current_month = rows[0].td.strong.text
        for tr in rows:
            tr_calendar = tr.find("td", class_="td-calendar")
            current_year = current_year if tr_calendar.text.strip() == "" \
                else tr_calendar.small.text
            current_month = current_month if tr_calendar.text.strip() == "" \
                else tr_calendar.strong.text
            day = tr.find("td", class_="td-day").text.strip()
            film_title = tr.find("td", class_="td-film-details").text.strip()
            film_year = tr.find("td", class_="td-released").text
            rating = tr.find("td", class_="td-rating")\
                .text.replace("×", " ").strip()
            like = True if \
                tr.find("td", class_="td-like") \
                .find("span", class_="has-icon icon-16 large-liked icon-liked hide-for-owner")\
                else False
            rewatch = False if \
                tr.find("td", class_="td-rewatch center icon-status-off") \
                else True
            film_slug = tr.find("td", class_="td-film-details")\
                .div["data-film-slug"]
            diary_entries.append(
                DiaryEntry(
                    f"{current_year}-{current_month}-{day}",
                    film_title,
                    int(film_year) if film_year else None,
                    rating,
                    like,
                    rewatch,
                    film_slug
                )
            )
        self._diary[str(page)] = diary_entries
        return diary_entries

    def print_info(self):
        print(f"Username: {self.username}")
        print(f"Profile URL: {self.profile_url}")
        print(f"Profile Name: {self.profile_name}")
        print(f"Total Films: {self.total_films}")
        print(f"Total Films This Year: {self.total_films_this_year}")
        print(f"Lists: {self.lists}")
        print(f"Following: {self.following}")
        print(f"Followers: {self.followers}")
        print(f"Pro: {self.pro}")

    def __repr__(self) -> str:
        return f"LetterboxdUser(username={self.username})"
