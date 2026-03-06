from dataclasses import dataclass

from pyulib import exceptions


@dataclass(frozen=True)
class PackageVersion:
    major: int
    minor: int
    patch: int
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def __lt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
    
    def __le__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)
    
    def __gt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)
    
    def __ge__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)
    
    def __eq__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))
    
    @classmethod
    def from_str(cls, st: str):
        parts = st.split(".")
        if len(parts) != 3:
            raise exceptions.InvalidVersion(f"Not 3 parts long! (Your length: {len(parts)})")
        try:
            parts = [int(p) for p in parts]
        except ValueError:
            raise exceptions.InvalidVersion(f"{st}")
        return cls(*parts)