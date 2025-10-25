import balder

from balderhub.fileops.scenarios.abstract_scenario_base import AbstractScenarioBase
from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature, DirectoryCreatorFeature, \
    DirectoryDeleterFeature
from balderhub.fileops.lib.utils import DirectoryItem


class ScenarioDirDeleteStandalone(AbstractScenarioBase):
    """
    Standalone scenario that provides test for DELETING directories.

    This standalone version also creates a test directory to delete.
    """

    class Filesystem(AbstractScenarioBase.Filesystem):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
        dir_creator = DirectoryCreatorFeature()   # TODO another scenario with already provided dirs??
        dir_deleter = DirectoryDeleterFeature()

    @balder.fixture('testcase')
    def dir_to_delete(self):
        """fixture that creates and cleans up a test directory"""
        directory = DirectoryItem('dir_to_delete')
        self.Filesystem.dir_creator.create_new_directory(directory.name)
        return directory

    def test_delete_empty_directory(self, dir_to_delete):
        """
        Simple test that tries to delete the test directory.
        """
        items_before = self.Filesystem.navigator.get_all_list_items()

        assert dir_to_delete in items_before, \
            f"can not find the {dir_to_delete} that should be deleted in {items_before}"

        self.Filesystem.dir_deleter.delete_directory(dir_to_delete)

        items_after = self.Filesystem.navigator.get_all_list_items()

        assert items_before.files == items_after.files, \
            f"the files should not change - before: {items_before.files} / after: {items_after.files}"

        assert len(items_after.dirs) == len(items_before.dirs) - 1, \
            f"detect unexpected number of directories: {len(items_after.dirs)} (expected {len(items_before.dirs) - 1})"

        dirs_deleted = items_before.dirs.subtract(items_after.dirs)
        assert len(dirs_deleted) == 1, (f"detect unexpected number of deleted directories: {dirs_deleted} "
                                        f"(expected `['{dir_to_delete}']`)")

        assert dirs_deleted[0] == dir_to_delete, f"detect unexpected directory: {dirs_deleted[0]}"

    #def test_delete_directory_with_other_dirs(self):
    #    pass
