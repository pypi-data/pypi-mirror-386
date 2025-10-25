import balder

from balderhub.fileops.lib.utils import DirectoryItem


class DirectoryDeleterFeature(balder.Feature):
    """
    Feature that allows to delete a directory within the filesystem
    """

    def delete_directory(self, directory: DirectoryItem) -> None:
        """
        This method deletes a directory from the filesystem.

        :param directory: the directory to delete
        """
        raise NotImplementedError()
