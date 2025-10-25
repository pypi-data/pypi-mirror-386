import pathlib

import balder

from ..utils.file_system_item_list import FileSystemItemList


class FileSystemNavigatorFeature(balder.Feature):
    """
    Feature that allows to navigate in the filesystem and allows to returns a list of the elements of the current
    active path
    """
    def navigate_to(self, path: pathlib.Path) -> None:
        """
        This method navigates to the specified path

        :param path: the path in the filesystem to navigate to
        """
        raise NotImplementedError()

    def get_all_list_items(self) -> FileSystemItemList:
        """
        This method returns a list of the files/directories at the current path in the filesystem

        :return: a :class:`FileSystemItemList` list with all items at the current path in the filesystem
        """
        raise NotImplementedError()
