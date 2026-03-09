from pathlib import Path
import os, shutil
from . import units

PARENT = Path(__file__).parent.parent
CONFIG_FILE = (PARENT / "config.yaml")
CACHE = (PARENT / "cache")
TESTS = (PARENT / "tests")
PACKAGES = (PARENT / "libs")

if CACHE.exists():
    shutil.rmtree(CACHE.absolute())

CACHE.mkdir(exist_ok=True)
TESTS.mkdir(exist_ok=True)
PACKAGES.mkdir(exist_ok=True)
import tempfile
tempfile.tempdir = str(CACHE.absolute())
#other shit

MAX_SIZE = "10 MiB"
MAX_UNCOMPRESSED_SIZE = "100 MiB"

MAX_SIZE = units.unit_to_num(MAX_SIZE)
MAX_UNCOMPRESSED_SIZE = units.unit_to_num(MAX_UNCOMPRESSED_SIZE)