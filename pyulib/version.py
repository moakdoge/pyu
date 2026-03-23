from dataclasses import dataclass
import re
_CACHED = re.compile(
    r"^(?:v)?(?:(\d+)!)?(\d+(?:[._-]\d+)*)(?:[-._]?([a-zA-Z]+)(\d+)?)?$"
)


_ALLOWED_TAGS = ["rc", "b", "a", "dev"][::-1]

@dataclass()
class PackageVersion:
    major: int
    minor: int
    patch: int
    epoch: int = 0
    tag: str = ""
    tag_version: int = 0

    def __post_init__(self):
        _allowed = False
        if self.tag == "":
            self.tag_version = -1
            return
        
        
    def __str__(self):
        base = f"{self.major}.{self.minor}.{self.patch}"
        t=self.tag_version if self.tag_version else ""
        p1=base + "-" + self.tag + str(t) if self.tag else base
        p0 = f"{self.epoch}!" if self.epoch > 0 else ""
        return p0 + p1
    
    def __lt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple < other.tuple 
    
    def __le__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple <= other.tuple 
    
    def __gt__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple > other.tuple 
    
    def __ge__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple >= other.tuple 
    
    def __eq__(self, other):
        if isinstance(other, str):
            other = PackageVersion.from_str(other)
        return self.tuple == other.tuple 
    
    def __hash__(self) -> int:
        return hash(self.tuple)
        
    @classmethod
    def from_str(cls, st: str):
        match = _CACHED.match(st)
        if not match:
            raise ValueError("Invalid version string!")

        epoch = int(match.group(1)) if match.group(1) else 0
        nums = match.group(2).split(".")
        tag = match.group(3) or ""
        tag_version = int(match.group(4) or 0)

        major = int(nums[0])
        minor = int(nums[1]) if len(nums) > 1 else 0
        patch = int(nums[2]) if len(nums) > 2 else 0

        return cls(major, minor, patch, tag=tag, epoch=epoch, tag_version=tag_version)

        
    def bump(self, type: str = "patch"):
        epoch = int(self.epoch)
        part1 = int(self.major)
        part2 = int(self.minor)
        part3 = int(self.patch)
        tag_version = int(self.tag_version)
        tag = self.tag
        match type:
            case "epoch":
                epoch += 1
            case "patch":
                part3 += 1
            case "minor":
                part3 = 0
                part2 += 1
            case "major":
                part3 = 0
                part2 = 0
                part1 += 1
            case "tag":
                tag_version = 0

                if tag not in _ALLOWED_TAGS:
                    tag = _ALLOWED_TAGS[0]

                if  _ALLOWED_TAGS.index(tag)+1 == len(_ALLOWED_TAGS):
                    tag = ""
                    part3 += 1
                
                else:
                    tag = _ALLOWED_TAGS[_ALLOWED_TAGS.index(tag) + 1]
            case "pre-release":
                if tag not in _ALLOWED_TAGS:
                    raise TypeError(f"`pre-release` bump is not possible unless you have a tag!")
                tag_version += 1
            case _:
                raise TypeError(f"Unknown bump type!")
        if part3 >= 100:
            part3 = 0
            part2 += 1
            if part2 >= 100:
                part2 = 0
                part1 += 1
        return PackageVersion(major=part1, minor=part2, patch=part3, tag=tag, tag_version=tag_version, epoch=epoch)
    
    @property
    def tuple(self):
        tag_priority = _ALLOWED_TAGS.index(self.tag) if self.tag in _ALLOWED_TAGS else -1
        return (self.epoch, self.major, self.minor, self.patch, tag_priority, self.tag_version)
    def __iter__(self):
        yield from self.tuple