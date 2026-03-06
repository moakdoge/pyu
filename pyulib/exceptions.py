from pathlib import Path

#packages
class PackageNotFound(Exception):
    def __init__(self, package: str):
        super().__init__(f"Package {package} was not found.")
class PackageCorrupted(Exception):
    def __init__(self, package: str, corruption: str = "Unknown") -> None:
        super().__init__(f"Package {package} is corrupted; Reason: {corruption}")
class InvalidPackage(Exception):
    def __init__(self, folder: str | Path, reason: str = "Unknown") -> None:
        super().__init__(f"Package at {folder.name if isinstance(folder, Path) else folder} is an invalid package: {reason}")

#metdata
class InvalidMetadata(Exception):
    def __init__(self, corruption: str = "Unknown") -> None:
        super().__init__(f"Metadata is corrupted! Reason: {corruption}")
class InvalidVersion(Exception):
    def __init__(self, provided: str) -> None:
        super().__init__(f"Please make sure your version string is in the right format! (major.minor.patch): Your input: {provided}")
