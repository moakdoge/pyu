import io
from pathlib import Path
import shutil
import time
import zipfile, json, re

from pyulib import files, other
from .version import PackageVersion
from . import config, exceptions


def generate_cache():
    data = {}

    for file in config.PACKAGES.glob("*.zip"):
        meta = validate_package(file)
        data[file.name] = {
            "name": meta.name,
            "author": meta.author,
            "version": str(meta.version),
            "depends": meta.depends
        }
    with open(config.PACKAGES / "cache.json", "w") as f:
        f.write(json.dumps(data, indent=2))

def load_cache():
    if not (config.PACKAGES / "cache.json").exists():
        generate_cache()

    with open(config.PACKAGES / "cache.json", "r") as file:
        return json.loads(file.read())
    
def validate_package(folder: Path | str | zipfile.ZipFile):
    from .metadata import PackageMetadata
    _tmp = None
    metadata = None
    #convert folder from str to path or zipfile to path
    if isinstance(folder, str):
        folder = Path(folder)
        metadata=(folder / "metadata.json").read_text()

    if isinstance(folder, zipfile.ZipFile):
        _tmp = folder
        folder = Path(files.tempfolder())
        metadata=_tmp.read("metadata.json").decode(errors="ignore")   

    elif isinstance(folder, Path) and zipfile.is_zipfile(folder):
        _tmp = folder
        folder = Path(files.tempfolder())
        with zipfile.ZipFile(_tmp) as z:
            metadata=z.read("metadata.json").decode(errors="ignore")
    
    elif isinstance(folder, Path):
        metadata=(folder / "metadata.json").read_text()
    

    if metadata is None:
        raise exceptions.InvalidPackage(folder, reason="Missing metadata.json!")
    
    d = json.loads(metadata)
    #remove tmp folder
    if _tmp is not None:
        shutil.rmtree(folder)

    return PackageMetadata.from_dict(d)

def find_depends(package: str, ver_prov: PackageVersion | None = None):
    '''TAKES IN A PACKAGE NAME!!'''
    from .files import ZipExtractor
    from .metadata import PackageMetadata
    depends = set()
    dps = {}
    cached = load_cache()
    comped = re.compile(r'^(>=|<=|>|<|=)?\s*([0-9]+(?:\.[0-9]+)*)')
    metadata = PackageMetadata.from_package(package)
    
    for lib, version in metadata.depends.items():
        matched = comped.match(version)
        operator = ""
        if matched:
            version = PackageVersion.from_str(matched.group(2))
            operator = matched.group(1)
        else:
            raise TypeError("Invalid operator!")
        
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
                    raise TypeError("Invalid operator!")
        if lib in dps:
            if dps[lib] != str(version):
                raise NotImplementedError("Multiple versions of the same package are unsupported!")
        else:
            dps[lib]=str(version)

        dps.update(find_depends(lib, version)) # type: ignore
    return dps

def locate_package(package_name: str, version: PackageVersion | None = None) -> Path:
    cached = load_cache()
    newest: tuple[str, PackageVersion] | None = None

    for zipped, data in cached.items():
        if data["name"] != package_name:
            continue

        contents = data.get("version")
        if not contents:
            raise exceptions.PackageCorrupted("Missing version field!")

        v = PackageVersion.from_str(contents)

        if version is not None:
            if v == version:
                return config.PACKAGES / zipped
            continue

        if newest is None or v > newest[1]:
            newest = (zipped, v)

    if newest is None:
        raise exceptions.PackageNotFound(package_name)

    return config.PACKAGES / newest[0]


def zip_packages(packages: dict[str, str], output_folder: Path | None = None) -> Path | tuple[bytes, str]:
    tmp = io.BytesIO()
    with zipfile.ZipFile(tmp, "w") as z:
        name=""
        for package, ver in packages.items():
            version_number = PackageVersion.from_str(ver)
            located_package: Path | None = locate_package(package, version=version_number)
            if located_package:
                z.write(located_package.absolute(), located_package.name)
            else:
                raise ()
            name += other.hash(package) + other.hash(ver)

        name = other.hash(name)
        import datetime
        metadata = {
            "hash": name,
            "created_on": datetime.datetime.now().isoformat(),
            "package_count": len(packages.keys()),
            "packages": dict(packages.items())
        }
        f = json.dumps(metadata, indent=2)
        z.writestr("package.json", data=f)
    _file_name = f"bundle-{name}.zip"
    if output_folder:
        with open(output_folder / _file_name, "wb") as f:
            f.write(tmp.getvalue())
        return (output_folder / _file_name)
    else:
        return (tmp.getvalue(), _file_name)