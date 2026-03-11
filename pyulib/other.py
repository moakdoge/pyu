import hashlib,zlib
from typing import Any
import re

__COMPILED_REGEX: dict[str, re.Pattern] = {}
def compile_regex(regex) -> re.Pattern:
    if regex not in __COMPILED_REGEX:
        __COMPILED_REGEX[regex] = re.compile(regex)
    return __COMPILED_REGEX[regex]
    

def beautify_name(name: str):
    name = name.lower()
    name = name.replace(" ", "_")
    name = re.sub(compile_regex(r"[^a-z0-9_-]"), "", name)
    return name

def hash(data: Any) -> str:
    d = str(data).encode()
    h = zlib.crc32(d)
    return f"{h:08x}"
    