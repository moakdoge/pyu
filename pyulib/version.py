from dataclasses import dataclass


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
            raise TypeError(f"Too little detail in versions!")
        try:
            parts = [int(p) for p in parts]
        except ValueError:
            raise ValueError(f"Please make sure all version numbers have only numbers!")
        return cls(*parts)