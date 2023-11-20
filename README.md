# Letterboxd Collage Maker

Scraping user profiles Letterboxd.com and creating collages from user diaries.

## Usage

Before anything, install the dependencies.
```bash
pip install -r requirements.txt
```
### Command Line
```bash
python letterboxdcollage.py <username>
```
This, by default, creates a 5x5 collage for ```username```. To make one in a different size, supply ```WIDTH``` and ```HEIGHT``` to --size.
```bash
python letterboxdcollage.py <username> --size 10 5
```
This create a 10x5 collage.

Currently, the maximum amount of films you can have in a collage is 50, so limit ```WIDTH``` and ```HEIGHT``` so that ```WIDTH*HEIGHT <= 50```
