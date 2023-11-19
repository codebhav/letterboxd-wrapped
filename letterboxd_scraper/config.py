import os
from pathlib import Path
from dataclasses import dataclass

POSTER_DIR = Path(".").absolute() / "posters"
try:
    os.mkdir(Path(__file__).parent.parent.resolve() / "posters")
    POSTER_DIR = Path(__file__).parent.parent.resolve() / "posters"
except FileExistsError:
    """posters directory already exists"""
    pass

@dataclass
class IMG_DIM:
    width = 230
    height = 345
