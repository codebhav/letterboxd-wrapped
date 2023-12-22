# Letterboxd Collage Maker

Scraping user profiles Letterboxd.com and creating collages from user diaries.

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