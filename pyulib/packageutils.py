from pathlib import Path
import zipfile, json
from .version import PackageVersion

PACKAGE_DIR = Path("/home/moakdoge/Desktop/pyu/server/libs")

def generate_cache():
    data = {}
    for file in PACKAGE_DIR.glob("*.zip"):
        with zipfile.ZipFile(file, "r") as z:
            contents = z.read("VERSION").decode()
            name = json.loads(z.read("metadata.json").decode())["name"]
            data[file.name] = {
                "name": name,
                "version": contents
            }
    with open(PACKAGE_DIR / "cache.json", "w") as f:
        f.write(json.dumps(data, indent=2))

def load_cache():
    if not (PACKAGE_DIR / "cache.json").exists():
        generate_cache()

    with open(PACKAGE_DIR / "cache.json", "r") as file:
        return json.loads(file.read())
    
def locate_package(package_name: str, version: PackageVersion | None = None) -> Path | None:
    cached = load_cache()
    last: tuple[Path | None, PackageVersion | None] = (None, None)
    for zipped, data in cached.items():
        contents = data["version"]
        name = data["name"]
        if name != package_name:
            continue
        if version:
            if not contents:
                raise Exception("Invalid package!")
            v = PackageVersion.from_str(contents)
            if version == v:
                return Path(PACKAGE_DIR / zipped)
        if last != (None, None):
            if PackageVersion.from_str(contents) > last[1]:
                last = (zipped, PackageVersion.from_str(contents))
        else:
            last = (zipped, PackageVersion.from_str(contents))
        
    return Path(PACKAGE_DIR / last[0]) # pyright: ignore[reportOperatorIssue]

                