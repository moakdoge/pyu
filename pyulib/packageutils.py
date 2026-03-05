from pathlib import Path
import shutil
import zipfile, json, re

from pyulib import files, other
from .version import PackageVersion

PACKAGE_DIR = Path("/home/moakdoge/Desktop/pyu/server/libs")
if not PACKAGE_DIR.exists():
    PACKAGE_DIR.mkdir()
def generate_cache():
    data = {}
    for file in PACKAGE_DIR.glob("*.zip"):
        with zipfile.ZipFile(file, "r") as z:
            contents = z.read("VERSION").decode()
            name = json.loads(z.read("metadata.json").decode())
            data[file.name] = {
                "name": name["name"],
                "version": contents,
                "depends": name.get("depends", {})
            }
    with open(PACKAGE_DIR / "cache.json", "w") as f:
        f.write(json.dumps(data, indent=2))

def load_cache():
    if not (PACKAGE_DIR / "cache.json").exists():
        generate_cache()

    with open(PACKAGE_DIR / "cache.json", "r") as file:
        return json.loads(file.read())
    
def find_depends(package: str, ver_prov: PackageVersion | None = None):
    '''TAKES IN A PACKAGE NAME!!'''
    from .files import ZipExtractor
    depends = set()
    dps = {}
    cached = load_cache()
    comped = re.compile(r'^(>=|<=|>|<|=)?\s*([0-9]+(?:\.[0-9]+)*)')
    pkg = locate_package(package)
    with ZipExtractor(pkg) as z:
        with open(z / "metadata.json", "r") as m:
            c=json.loads(m.read())
            depends = c.get("depends", {})
    for lib, version in depends.items():
        matched = comped.match(version)
        operator = ""
        if matched:
            version = PackageVersion.from_str(matched.group(2))
            operator = matched.group(1)
        else:
            raise Exception("Invalid operator!")
        for zipped, data in cached.items():
            vv = PackageVersion.from_str(data["version"])
            name = data["name"]
            if ver_prov is not None:
                if vv != ver_prov:
                    continue
            if name != lib:
                continue
            match operator:
                case ">=":
                    if vv >= version:
                        version = vv
                        break
                case "<=":
                    if vv <= version:
                        version = vv
                        break
                case ">":
                    if vv > version:
                        version = vv
                        break
                case "<":
                    if vv < version:
                        version = vv
                        break
                case "=":
                    if vv == version:
                        version = vv
                        break
                case _:
                    raise Exception("Invalid operator!")
        if lib in dps:
            if dps[lib] != str(version):
                raise NotImplementedError("Multiple versions of the same package are unsupporteD!")
        else:
            dps[lib]=str(version)

        dps.update(find_depends(lib, version)) # type: ignore
    return dps

def locate_package(package_name: str, version: PackageVersion | None = None) -> Path | None:
    cached = load_cache()
    newest: tuple[str, PackageVersion] | None = None

    for zipped, data in cached.items():
        if data["name"] != package_name:
            continue

        contents = data.get("version")
        if not contents:
            raise Exception("Invalid package!")

        v = PackageVersion.from_str(contents)

        if version is not None:
            if v == version:
                return PACKAGE_DIR / zipped
            continue

        if newest is None or v > newest[1]:
            newest = (zipped, v)

    if newest is None:
        return None

    return PACKAGE_DIR / newest[0]


def zip_packages(packages: dict[str, str], output_folder: Path):
    tmpfolder = Path(files.tempfolder())
    name=""
    for package, ver in packages.items():
        version_number = PackageVersion.from_str(ver)
        located_package: Path | None = locate_package(package, version=version_number)
        if located_package:
            shutil.copyfile(located_package.absolute(), tmpfolder / located_package.name)
        else:
            raise FileNotFoundError(f"Package {package} (v{ver}) not found!")
        name += other.hash(package) + other.hash(ver)

    name = other.hash(name)
    with open(tmpfolder / "packages.json", "w") as f:
        import datetime
        metadata = {
            "hash": name,
            "created_on": datetime.datetime.now().isoformat(),
            "package_count": len(packages.keys()),
            "packages": dict(packages.items())
        }
        f.write(json.dumps(metadata, indent=2)) 
    
    files.zipfolder(tmpfolder,output_folder / f"bundle-{name}.zip")