import tempfile
import zipfile

from pyulib import exceptions

from . import files, packageutils, other, labels, config
import time, json, shutil
from pathlib import Path
from dataclasses import dataclass, field
from .version import PackageVersion



@dataclass(frozen=False)
class PackageMetadata:
    name: str
    version: PackageVersion
    author: str
    depends: dict[str, str] = field(default_factory=dict)
    @classmethod
    def from_dict(cls, d: dict):
        name = d.get("name", None)
        if not name:
            raise exceptions.InvalidMetadata(f"Name field missing!")
        author = d.get("author", "N/A")
        version = d.get("version", None)
        if version is None:
            raise exceptions.InvalidMetadata(f"Metadata {name} is missing a `version` field!")
        depends = d.get("depends", {})
        return cls(name=name, author=author, version=PackageVersion.from_str(version), depends=depends)
    @classmethod
    def from_package(cls, package: str):
        pack = packageutils.locate_package(package)

        with zipfile.ZipFile(pack, mode="r") as zipped:
            return packageutils.validate_package(zipped)
    
    def __post_init__(self):
        self.name = other.beautify_name(self.name)
class Package:
    def __init__(self, package: str, version: str | PackageVersion | None = None):
        if isinstance(version, str):
            version = PackageVersion.from_str(version)
        
        file = packageutils.locate_package(package, version=version)
        self._file = file

        with files.ZipExtractor(file_name=file.name, file_bytes=file.read_bytes()) as zipped:
            self._metadata = packageutils.validate_package(file)
            self._version = self._metadata.version
    
    @classmethod
    def generate_package(cls, folder: Path):
        from . import packageutils
        if not folder.exists():
            raise FileNotFoundError(f"Folder {folder.absolute()} does not exist! Cannot make package.")
        
        with tempfile.TemporaryDirectory() as __tmp:
            tmpfolder = Path(__tmp)
            for item in folder.iterdir():
                target = tmpfolder / item.name
                if item.is_dir():
                    shutil.copytree(item, target, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, target)
            
            with files.tempfile("/tmp") as f:
                zip_path = f.name + ".zip"
                meta = packageutils.validate_package(folder)
                watermark_file = tmpfolder / "WATERMARK"
                watermark_file.write_text(labels.WATERMARK)

                files.zipfolder(tmpfolder, zip_path)
                shutil.copyfile(zip_path, Path(config.PACKAGES/ f"{other.beautify_name(meta.name)}-{str(meta.version)}.zip"))
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


def cache():
    for file in config.TESTS.glob("*"):
        if file.is_file():
            continue
        Package.generate_package(file)
    packageutils.generate_cache()