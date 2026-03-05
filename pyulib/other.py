import hashlib,zlib
from typing import Any


def beautify_name(name: str):
    name = name.title()
    name = name.replace(" ", "")
    return name



def hash(data: Any) -> str:
    d = str(data).encode()
    h = zlib.crc32(d)
    return f"{h:08x}"
    