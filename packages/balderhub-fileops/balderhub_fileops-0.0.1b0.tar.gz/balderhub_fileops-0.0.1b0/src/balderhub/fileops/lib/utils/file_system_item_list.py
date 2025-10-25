from __future__ import annotations
from .file_system_item import FileSystemItem, FileSystemItemTypeT
from .file_item import FileItem
from .directory_item import DirectoryItem


class FileSystemItemList(list):
    """
    Helper class to work with a list of :class:`FileSystemItem`
    """

    def filter_by(self, file_system_item_type: type[FileSystemItemTypeT]):
        """
        Filters the current item list by a specific type of :class:`FileSystemItem`

        :param file_system_item_type: the requested type the filter should be applied for
        :return: the new filtered list
        """
        if not isinstance(file_system_item_type, type) and issubclass(file_system_item_type, FileSystemItem):
            raise TypeError(f'file_system_item_type must be a subclass of `{FileSystemItem.__name__}`')
        return self.__class__(filter(lambda item: isinstance(item, file_system_item_type), self))

    @property
    def dirs(self):
        """
        :return: filters the list by :class:`DirectoryItem` only
        """
        return self.filter_by(DirectoryItem)

    @property
    def files(self):
        """
        :return: filters the list by :class:`FileItem` only
        """
        return self.filter_by(FileItem)

    def has_duplicates(self) -> bool:
        """
        :return: returns True if the list has duplicate items
        """
        return len(self) != len(set(self))

    def compare_with(self, other: FileSystemItemList, ignore_order=False):
        """
        This method compares two :class:`FileSystemItemList`.

        :param other: the other :class:`FileSystemItemList` to compare with
        :param ignore_order: True if the order is not relevant and can be ignored during comparison
        :return: True if the lists are equal, False otherwise
        """
        this_list = self.copy()
        other_list = other.copy()
        if ignore_order:
            this_list = sorted(this_list, key=lambda f: f.name)
            other_list = sorted(other_list, key=lambda f: f.name)

        return this_list == other_list

    def subtract(self, other: FileSystemItemList, ignore_non_existing: bool = False):
        """
        This method subtracts two :class:`FileSystemItemList` from each other.
        :param other: the other :class:`FileSystemItemList` to subtract
        :param ignore_non_existing: True if the method should not throw an exception in case that the other list has
                                    elements that are not contained in this list
        :return: a :class:`FileSystemItemList` with elements that are are contained in this list, but not in the other
                 list
        """
        if self.has_duplicates():
            raise ValueError('this list has duplicates - can only apply the `subtract()` method for unique lists')
        if other.has_duplicates():
            raise ValueError('the provided list `other` has duplicates - can only apply the `subtract()` method for '
                             'unique lists')
        if not ignore_non_existing:
            for elem in other:
                if elem not in self:
                    raise ValueError(f'cannot subtract {elem} from {self}, because it does not exist')

        diff = set(self) - set(other)
        return self.__class__(diff)
