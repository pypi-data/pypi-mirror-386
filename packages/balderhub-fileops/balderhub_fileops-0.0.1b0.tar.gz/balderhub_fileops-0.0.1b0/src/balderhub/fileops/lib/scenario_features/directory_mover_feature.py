import pathlib
from typing import Union

import balder

from balderhub.fileops.lib.utils import DirectoryItem


class DirectoryMoverFeature(balder.Feature):
    """
    Feature that allows to move a directory within the filesystem
    """
    def move_directory(self, source: DirectoryItem, destination: Union[DirectoryItem, pathlib.Path]) -> None:
        """
        This method moves a directory (provided by ``source``) to the destination directory.

        :param source: the directory to be moved
        :param destination: the destination directory
        """
        raise NotImplementedError()
