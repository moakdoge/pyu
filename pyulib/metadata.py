import asyncio
import tempfile
import threading
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
    language: str = ""

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
        l = d.get("language", "")
        return cls(name=name, author=author, version=PackageVersion.from_str(version), depends=depends, description=des, language=l)
    
    @classmethod
    def from_package(cls, package: str, version: PackageVersion | None = None):
        pack = packageutils.locate_package(package, version=version)
        return packageutils.get_metadata(pack)
    
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
            "description": self.description,
            "language": self.language
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
    

_LOCKED = {}
def lock_package(pack: str):
    if pack not in _LOCKED:
        _LOCKED[pack] = threading.Lock()
    return _LOCKED[pack]
    
class Package:
    def __init__(self, package: str, version: str | PackageVersion | None = None):
        if isinstance(version, str):
            version = PackageVersion.from_str(version)
        
        file = packageutils.locate_package(package, version=version)
        self._file = file

        with self.lock():
            with files.ZipExtractor(file_name=file.name, file_bytes=file.read_bytes()) as zipped:
                self._metadata = packageutils.get_metadata(file)
                self._version = self._metadata.version
    
    @classmethod
    async def agenerate_package(cls, folder: Path):
        return asyncio.to_thread(cls.generate_package, folder)
     
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
                meta = packageutils.get_metadata(folder)
                try:
                    packageutils.locate_package(meta.name, meta.version)
                    raise exceptions.PackageExists(meta.name, str(meta.version))
                except exceptions.PackageNotFound as e: #amazing way to detect if a package exists lmfao
                    pass
                
                watermark_file = tmpfolder / "WATERMARK"
                watermark_file.write_text(labels.WATERMARK)

                with lock_package(meta.name):
                    files.zipfolder(tmpfolder, zip_path)
                    meta.parent.mkdir(exist_ok=True)
                    shutil.move(zip_path, meta.path)
        packageutils.generate_cache()
    
    def lock(self):
        return lock_package(self.name)
    
    async def alock(self):
        def s():
            with lock_package(self.name):
                pass
        return await asyncio.to_thread(s)

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