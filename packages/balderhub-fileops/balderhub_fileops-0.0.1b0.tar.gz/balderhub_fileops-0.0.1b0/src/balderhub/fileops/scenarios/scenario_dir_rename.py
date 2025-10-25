import balder

from balderhub.fileops.scenarios.abstract_scenario_base import AbstractScenarioBase
from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature, DirectoryCreatorFeature, \
    DirectoryDeleterFeature, DirectoryRenamerFeature
from balderhub.fileops.lib.utils import DirectoryItem


class ScenarioDirRenameStandalone(AbstractScenarioBase):
    """
    Standalone scenario that provides test for RENAMING directories.

    This standalone version also creates a test directory to rename and cleans up everything afterward.
    """

    class Filesystem(AbstractScenarioBase.Filesystem):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
        dir_creator = DirectoryCreatorFeature()    # TODO another scenario with already provided dirs??
        dir_deleter = DirectoryDeleterFeature()    # TODO another scenario with already provided dirs??
        dir_rename = DirectoryRenamerFeature()

    @balder.fixture('testcase')
    def dir_to_rename(self):
        """fixture that creates and cleans up a test directory"""
        directory = DirectoryItem('dir_to_rename')
        self.Filesystem.dir_creator.create_new_directory(directory.name)
        yield directory
        if directory in self.Filesystem.navigator.get_all_list_items():
            self.Filesystem.dir_deleter.delete_directory(directory)

    def test_rename_directory(self, dir_to_rename):
        """
        Simple test that tries to rename the test directory. It will automatically clean up everything it changed
        afterward.
        """
        items_before = self.Filesystem.navigator.get_all_list_items()

        # now copy the first directory
        new_renamed_dir = DirectoryItem(f"{dir_to_rename.name}_renamed")

        assert new_renamed_dir not in items_before, \
            f"a`{new_renamed_dir}` already exists within elements {items_before}"

        try:
            self.Filesystem.dir_rename.rename_directory(dir_to_rename, new_renamed_dir.name)

            items_after = self.Filesystem.navigator.get_all_list_items()

            assert items_before.files == items_after.files, \
                f"different files detected - before {items_before.files} / after {items_after.files}"

            assert len(items_before.dirs) == len(items_after.dirs), \
                f"directory count should not change - before: {items_before.dirs} / after: {items_after.dirs}"

            assert dir_to_rename not in items_after.dirs, \
                f"{dir_to_rename} should not be available in file list after renaming: {items_after.dirs}"

            assert new_renamed_dir in items_after.dirs, \
                f"{new_renamed_dir} should be available  in file list after renaming: {items_after.dirs}"

            # todo make sure that content of `dir_to_move` is in `new_moved_dir`
        finally:
            if new_renamed_dir in self.Filesystem.navigator.get_all_list_items():
                self.Filesystem.dir_deleter.delete_directory(new_renamed_dir)
