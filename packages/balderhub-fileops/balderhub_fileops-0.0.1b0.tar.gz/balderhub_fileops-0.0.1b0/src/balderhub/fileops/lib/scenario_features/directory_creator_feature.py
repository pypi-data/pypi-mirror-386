import balder


class DirectoryCreatorFeature(balder.Feature):
    """
    Feature that allows to create a directory within the filesystem
    """
    def create_new_directory(self, name: str) -> None:
        """
        This method creates a new directory with the provided name

        :param name: the name of the new directory
        """
        raise NotImplementedError()
