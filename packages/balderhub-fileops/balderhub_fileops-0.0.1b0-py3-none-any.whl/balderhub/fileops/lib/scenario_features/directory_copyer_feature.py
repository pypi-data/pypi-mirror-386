import balder

from balderhub.fileops.lib.utils import DirectoryItem


class DirectoryCopyerFeature(balder.Feature):
    """
    Feature that allows to copy a directory within the filesystem
    """

    def copy_directory(self, source: DirectoryItem) -> str:
        """
        This method copies a directory and returns the new name of the directory.

        :param source: the directory that should be copied
        :return: the name of the copied directory
        """
        raise NotImplementedError()
