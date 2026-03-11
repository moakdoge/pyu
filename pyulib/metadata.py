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
    description: str = ""
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
        des = d.get("description", "")
        return cls(name=name, author=author, version=PackageVersion.from_str(version), depends=depends, description=des)
    
    @classmethod
    def from_package(cls, package: str):
        pack = packageutils.locate_package(package)
        return packageutils.validate_package(pack)
    
    @property
    def path(self):
        return config.PACKAGES / self.name / (str(self.version)+".zip")
    
    @property
    def parent(self):
        return self.path.parent
    
    @property
    def cache(self):
        return {
            "name": self.name,
            "author": self.author,
            "version": str(self.version),
            "depends": self.depends,
            "hash": self.hash,
            "description": self.description
        }

    @property
    def full_cache(self):
        x=self.cache.copy()
        x.update({"versions": [str(s) for s in self.versions]})
        return x
    
    def __post_init__(self):
        self.name = other.beautify_name(self.name)

    
    @property
    def hash(self):
        if not hasattr(self, "__cached_hash"):
            import hashlib
            if self.path.exists():
                self.__cached_hash = hashlib.md5(self.path.read_bytes()).digest().hex()
            else:
                self.__cached_hash = 0
        return self.__cached_hash

    @property
    def versions(self) -> list[PackageVersion]:
        vers = []
        for z in self.parent.glob("*.zip"):
            vers.append(PackageVersion.from_str(z.stem))
        return vers
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
                try:
                    packageutils.locate_package(meta.name, meta.version)
                    raise exceptions.PackageExists(meta.name, str(meta.version))
                except exceptions.PackageNotFound as e: #amazing way to detect if a package exists lmfao
                    pass
                
                watermark_file = tmpfolder / "WATERMARK"
                watermark_file.write_text(labels.WATERMARK)

                
                files.zipfolder(tmpfolder, zip_path)
                meta.parent.mkdir(exist_ok=True)
                shutil.copyfile(zip_path, meta.path)
        packageutils.generate_cache()

    @classmethod
    def search(cls, package_name: str, package_version: str):
        pass

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
    import os
    cache_file = config.PACKAGES / "cache.json"
    if cache_file.exists():
        os.remove(cache_file)
    for file in config.TESTS.glob("*"):
        if file.is_file():
            continue
        try:
            Package.generate_package(file)
        except exceptions.PackageExists:
            pass
    packageutils.generate_cache()