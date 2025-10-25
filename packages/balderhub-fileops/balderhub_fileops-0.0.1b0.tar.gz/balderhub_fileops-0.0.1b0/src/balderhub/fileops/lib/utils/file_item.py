import dataclasses
from .file_system_item import FileSystemItem


@dataclasses.dataclass
class FileItem(FileSystemItem):
    """
    describes a file
    """

    def __hash__(self):
        return hash(self.name)
