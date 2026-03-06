from pathlib import Path

from fastapi import HTTPException

#packages

class BaseHTTPException(Exception):
    __slots__ = ()
    status_code = 500
    def __init__(self, *args: object) -> None:
        self.__args = args 
        super().__init__(*args)

    def http_exception(self, status_code: int = 0) -> HTTPException:
        if status_code == 0:
            status_code = self.status_code
        return HTTPException(status_code=status_code, detail=str(self))
    
class PackageNotFound(BaseHTTPException):
    status_code=404
    def __init__(self, package: str):
        super().__init__(f"Package {package} was not found.")
class PackageCorrupted(BaseHTTPException):
    status_code=500
    def __init__(self, package: str, corruption: str = "Unknown") -> None:
        super().__init__(f"Package {package} is corrupted; Reason: {corruption}")
class InvalidPackage(BaseHTTPException):
    status_code=500
    def __init__(self, folder: str | Path, reason: str = "Unknown") -> None:
        super().__init__(f"Package at {folder.name if isinstance(folder, Path) else folder} is an invalid package: {reason}")

#metdata
class InvalidMetadata(BaseHTTPException):
    status_code=500
    def __init__(self, corruption: str = "Unknown") -> None:
        super().__init__(f"Metadata is corrupted! Reason: {corruption}")
class InvalidVersion(BaseHTTPException):
    status_code=500
    def __init__(self, provided: str) -> None:
        super().__init__(f"Please make sure your version string is in the right format! (major.minor.patch): Your input: {provided}")
