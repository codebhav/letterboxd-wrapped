import os
from pathlib import Path
from dataclasses import dataclass


POSTER_DIR = Path(__file__).parent.parent.resolve() / "posters"
if not POSTER_DIR.is_dir():
    os.mkdir(POSTER_DIR)

@dataclass
class IMG_DIM:
    width = 230
    height = 345
