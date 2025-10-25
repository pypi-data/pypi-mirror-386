import dataclasses
from .file_system_item import FileSystemItem


@dataclasses.dataclass
class DirectoryItem(FileSystemItem):
    """
    describes a directory
    """

    def __hash__(self):
        return hash(self.name)
