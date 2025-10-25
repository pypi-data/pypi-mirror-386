import balder

from balderhub.fileops.lib.utils import DirectoryItem


class DirectoryRenamerFeature(balder.Feature):
    """
    Feature that allows to rename a directory within the filesystem
    """
    def rename_directory(self, source: DirectoryItem, rename_to: str) -> None:
        """
        This method renames the directory provided with ``source`` to the name given with ``rename_to``.

        :param source: the source directory that should be renamed
        :param rename_to: the new name the source directory should be named to
        """
        raise NotImplementedError()
