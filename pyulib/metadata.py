from . import files, packageutils, other, labels
import time, json, shutil
from pathlib import Path
from dataclasses import dataclass
from .version import PackageVersion



@dataclass(frozen=True)
class PackageMetadata:
    name: str
    version: PackageVersion
    author: str

class Package:
    def __init__(self, package: str, version: str | PackageVersion | None = None):
        if isinstance(version, str):
            version = PackageVersion.from_str(version)
        file = packageutils.locate_package(package, version=version)
        if not file:
            raise FileNotFoundError(f"{package} not found!")
        self._file = file
        with files.ZipExtractor(file_name=file.name, file_bytes=file.read_bytes()) as zipped:
            ver = zipped / "VERSION"
            meta = zipped / "metadata.json"
            if not ver.exists() or not meta.exists():
                raise FileNotFoundError(f"Invalid package!")
            self._meta = json.loads(meta.read_text())
            self._version = ver.read_text()
        self._metadata = PackageMetadata(
            self._meta["name"],
            PackageVersion.from_str(self._version),
            self._meta["author"]
        )
    
    @classmethod
    def generate_package(cls, folder: Path):
        from . import packageutils
        if not folder.exists():
            raise FileNotFoundError(f"Folder {folder.absolute()} does not exist! Cannot make package.")
        tmpfolder = Path(files.tempfolder())
        for item in folder.iterdir():
            target = tmpfolder / item.name
            if item.is_dir():
                shutil.copytree(item, target, dirs_exist_ok=True)
            else:
                shutil.copy2(item, target)
        
        with files.tempfile("/tmp") as f:
            zip_path = f.name + ".zip"
            v = tmpfolder / "VERSION"
            n = tmpfolder / "metadata.json"

            if not v.exists() and n.exists():
                ver = json.loads(n.read_text()).get("version", None)
                if ver:
                    with open(tmpfolder / "VERSION", "w") as m:
                        m.write(ver)
            (tmpfolder / "WATERMARK").write_text(labels.WATERMARK)
            if not v.exists() or not n.exists():
                raise FileNotFoundError(f"Invalid package!")
            ver = PackageVersion.from_str(v.read_text())
            name = json.loads(n.read_text())["name"]
            files.zipfolder(tmpfolder, zip_path)
            shutil.copyfile(zip_path, Path(packageutils.PACKAGE_DIR / f"{other.beautify_name(name)}-{str(ver)}.zip"))
        packageutils.generate_cache()

    @property
    def version(self) -> PackageVersion:
        return self._metadata.version
    
    @property
    def name(self):
        return self._metadata.name
    
    @property
    def author(self):
        return self._metadata.author

    @property
    def metadata(self) -> PackageMetadata:
        return self._metadata
    
    @property
    def size(self):
        return self._file.lstat().st_size

    @property
    def creation(self):
        return self._file.lstat().st_ctime
    
    @property
    def modification(self):
        return self._file.lstat().st_mtime

def cache():
    for file in packageutils.TESTS_DIR.glob("*"):
        if file.is_file():
            continue
        Package.generate_package(file)
    packageutils.generate_cache()