from pathlib import Path
import os, shutil

PARENT = Path(__file__).parent.parent
CACHE = (PARENT / "cache")
TESTS = (PARENT / "tests")
PACKAGES = (PARENT / "libs")

if not PARENT.exists():
    class YouDumbass(Exception):    pass
    raise YouDumbass("You fucking dumbass.")
if CACHE.exists():
    shutil.rmtree(CACHE.absolute())
CACHE.mkdir(exist_ok=True)
TESTS.mkdir(exist_ok=True)
PACKAGES.mkdir(exist_ok=True)
import tempfile
tempfile.tempdir = str(CACHE.absolute())
#other shit

MAX_SIZE = 10_000_000 #10MB=-------