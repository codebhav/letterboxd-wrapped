import requests
from bs4 import BeautifulSoup
import time

from .film import Film, DiaryEntry

class LetterboxdUser:
    def __init__(self, username: str, diary_filters: dict={}):
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
        self.diary_filters = {
            "only-films": False,
            "hide-shorts": False,
            "hide-tv": False,
            "hide-docs": False
        } | diary_filters

    def _make_request(self, url, cookies=None):
        """Make request with proper headers and error handling"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        try:
            response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            raise

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
        try:
            res = self._make_request(self.profile_url)
            soup = BeautifulSoup(res.text, "html.parser")
            
            # Profile name
            profile_name_elem = soup.find("div", class_="profile-name-wrap")
            if profile_name_elem and profile_name_elem.h1:
                profile_name = profile_name_elem.h1.text.strip()
            else:
                profile_name = self.username
            
            # Profile statistics
            profile_statistics = []
            for stat in soup.find_all("h4", "profile-statistic"):
                stat_text = stat.text
                digits = "".join([c for c in stat_text if c.isdigit()])
                profile_statistics.append(int(digits) if digits else 0)
            
            # Ensure we have all 5 statistics (films, this year, lists, following, followers)
            while len(profile_statistics) < 5:
                profile_statistics.append(0)
            
            # Pro status
            pro = soup.find("span", class_="badge") is not None
            
            # Bio
            bio_elem = soup.find("section", id="person-bio") or soup.find("div", class_="bio")
            bio_text = ""
            if bio_elem and bio_elem.div:
                bio_text = bio_elem.div.get_text("\n", strip=True)
            
            # Four favorites
            ffaves = []
            for f in soup.find_all("li", class_="favourite-film-poster-container"):
                if f.div and f.div.get("data-film-slug"):
                    img_elem = f.div.find("img")
                    film_title = img_elem.get("alt", "Unknown") if img_elem else "Unknown"
                    ffaves.append(
                        Film(
                            film_title=film_title,
                            film_year=None,
                            film_slug=f.div["data-film-slug"]
                        )
                    )
            
            self._profile_name = profile_name
            self._total_films = profile_statistics[0] if len(profile_statistics) > 0 else 0
            self._total_films_this_year = profile_statistics[1] if len(profile_statistics) > 1 else 0
            self._lists = profile_statistics[2] if len(profile_statistics) > 2 else 0
            self._following = profile_statistics[3] if len(profile_statistics) > 3 else 0
            self._followers = profile_statistics[4] if len(profile_statistics) > 4 else 0
            self._pro = pro
            self._bio = bio_text
            self._four_faves = ffaves
            
        except Exception as e:
            print(f"Error fetching profile info: {e}")
            # Set defaults
            self._profile_name = self.username
            self._total_films = 0
            self._total_films_this_year = 0
            self._lists = 0
            self._following = 0
            self._followers = 0
            self._pro = False
            self._bio = ""
            self._four_faves = []

    def diary(self, page=1) -> list[DiaryEntry] | None:
        if str(page) in self._diary:
            return self._diary[str(page)]

        film_filter = ""
        for k, v in self.diary_filters.items():
            if k == "only-films" and v:
                film_filter = "hide-shorts%20hide-tv%20hide-docs"
                break
            if v:
                film_filter += f"{k}%20"

        print(f"Fetching diary entries on page {page}")
        print(f"Filters: {self.diary_filters}")
        
        diary_entries = []
        cookies = {"filmFilter": film_filter.strip("%20")} if film_filter else None
        
        try:
            res = self._make_request(
                self.profile_url + f"/films/diary/page/{page}",
                cookies=cookies
            )
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.find_all("tr", class_="diary-entry-row")

            if not rows:
                print(f"Diary page {page} does not exist or is empty")
                return None

            current_year = ""
            current_month = ""
            
            # Get initial year and month from first row
            first_row = rows[0]
            first_calendar = first_row.find("td", class_="td-calendar")
            if first_calendar:
                year_elem = first_calendar.find("small")
                month_elem = first_calendar.find("strong")
                if year_elem:
                    current_year = year_elem.text.strip()
                if month_elem:
                    current_month = month_elem.text.strip()

            for tr in rows:
                try:
                    tr_calendar = tr.find("td", class_="td-calendar")
                    if tr_calendar and tr_calendar.text.strip():
                        year_elem = tr_calendar.find("small")
                        month_elem = tr_calendar.find("strong")
                        if year_elem:
                            current_year = year_elem.text.strip()
                        if month_elem:
                            current_month = month_elem.text.strip()
                    
                    day_elem = tr.find("td", class_="td-day")
                    day = day_elem.text.strip() if day_elem else "1"
                    
                    film_details = tr.find("td", class_="td-film-details")
                    if not film_details:
                        continue
                        
                    film_title = film_details.text.strip()
                    film_slug = film_details.div.get("data-film-slug") if film_details.div else None
                    
                    if not film_slug:
                        continue
                    
                    released_elem = tr.find("td", class_="td-released")
                    film_year = released_elem.text.strip() if released_elem else None
                    film_year = int(film_year) if film_year and film_year.isdigit() else None
                    
                    rating_elem = tr.find("td", class_="td-rating")
                    rating = rating_elem.text.replace("×", " ").strip() if rating_elem else ""
                    
                    like_elem = tr.find("td", class_="td-like")
                    like = bool(like_elem and like_elem.find("span", class_="icon-liked"))
                    
                    rewatch_elem = tr.find("td", class_="td-rewatch")
                    rewatch = not bool(rewatch_elem and "icon-status-off" in rewatch_elem.get("class", []))
                    
                    diary_entries.append(
                        DiaryEntry(
                            f"{current_year}-{current_month}-{day}",
                            film_title,
                            film_year,
                            rating,
                            like,
                            rewatch,
                            film_slug
                        )
                    )
                except Exception as e:
                    print(f"Error parsing diary entry: {e}")
                    continue

            self._diary[str(page)] = diary_entries
            time.sleep(0.5)  # Be nice to the server
            return diary_entries
            
        except Exception as e:
            print(f"Error fetching diary page {page}: {e}")
            return None

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
