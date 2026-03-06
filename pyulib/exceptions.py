from pathlib import Path


class PackageNotFound(Exception):
    def __init__(self, package: str):
        super().__init__(f"Package {package} was not found.")
class PackageCorrupted(Exception):
    def __init__(self, package: str, corruption: str = "Unknown") -> None:
        super().__init__(f"Package {package} is corrupted; Reason: {corruption}")
class InvalidPackage(Exception):
    def __init__(self, folder: str | Path, reason: str = "Unknown") -> None:
        super().__init__(f"Package at {folder.name if isinstance(folder, Path) else folder} is an invalid package: {reason}")
def throw(excp: BaseException):
    raise excp