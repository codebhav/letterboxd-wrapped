# Letterboxd Collage Maker

Scraping user profiles [Letterboxd.com](https://letterboxd.com) and creating collages from user diaries.

![letterboxd-collage.jpg](https://geraldsaberon.github.io/images/letterboxd-collage.jpg)

## Usage

Before anything, install the dependencies.
```bash
pip install -r requirements.txt
```
### Command Line
```bash
python collage.py <username>
```
This, by default, creates a 5x5 collage for ```username```. To make one in a different size, supply ```WIDTH``` and ```HEIGHT``` to --size.
```bash
python collage.py <username> --size 10 10
```
The maximum collage size is 10x10.

You can also use these options to filter diary entries.
```
--hide-shorts, -s  Exclude short films from collage
--hide-tv, -t      Exclude TV shows from collage
--hide-docs, -d    Exclude documentaries from collage
--only-films, -f   Only include feature-length films in collage (exclude short films, TV shows, and documentaries)
```

### Web App
You can use the web app too locally.

```bash
flask --app app/server.py run
```