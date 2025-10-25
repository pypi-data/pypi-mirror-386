from typing import TypeVar
import dataclasses


FileSystemItemTypeT = TypeVar('FileSystemItemTypeT', bound='FileSystemItem')

@dataclasses.dataclass
class FileSystemItem:
    """
    base class for elements that can be located inside the filesystem
    """
    name: str

    def __eq__(self, other):
        return self.__class__ == self.__class__ and self.name == other.name

    def __hash__(self):
        return hash(self.name)
