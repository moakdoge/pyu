from pathlib import Path


PARENT = Path(__file__).parent.parent
CACHE = (PARENT / "CACHE")
TESTS = (PARENT / "TESTS")
PACKAGES = (PARENT / "libs")

if not PARENT.exists():
    class YouDumbass(Exception):    pass
    raise YouDumbass("You fucking dumbass.")

CACHE.mkdir(exist_ok=True)
TESTS.mkdir(exist_ok=True)
PACKAGES.mkdir(exist_ok=True)

#other shit

MAX_SIZE = 10_000_000 #10MB