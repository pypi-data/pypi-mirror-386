import balder

from balderhub.fileops.scenarios.abstract_scenario_base import AbstractScenarioBase
from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature, DirectoryCreatorFeature, \
    DirectoryCopyerFeature, DirectoryDeleterFeature
from balderhub.fileops.lib.utils import DirectoryItem


class ScenarioDirCopyStandalone(AbstractScenarioBase):
    """
    Standalone scenario that provides test for COPYING directories.

    This standalone version also creates a test directory to copy and cleans up everything afterward.
    """
    class Filesystem(AbstractScenarioBase.Filesystem):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
        dir_creator = DirectoryCreatorFeature()    # TODO another scenario with already provided dirs??
        dir_deleter = DirectoryDeleterFeature()  # TODO another scenario with already provided dirs??
        dir_copyer = DirectoryCopyerFeature()

    @balder.fixture('testcase')
    def dir_to_copy(self):
        """fixture that creates and cleans up a test directory"""
        directory = DirectoryItem('dir_that_should_be_copied')
        self.Filesystem.dir_creator.create_new_directory(directory.name)
        yield directory
        self.Filesystem.dir_deleter.delete_directory(directory)

    def test_copy_directory(self, dir_to_copy):
        """
        Simple test that tries to copy the test directory. It will automatically clean up everything it changed
        afterward.
        """
        items_before = self.Filesystem.navigator.get_all_list_items()

        # now copy the first directory
        new_copied_dir = DirectoryItem(self.Filesystem.dir_copyer.copy_directory(dir_to_copy))
        try:
            assert new_copied_dir not in items_before, f"copied `{new_copied_dir}` already exists"

            items_after = self.Filesystem.navigator.get_all_list_items()

            assert len(items_before.dirs) + 1 == len(items_after.dirs), \
                (f"expected {len(items_before.dirs) + 1} directories, but got {len(items_after.dirs)}: "
                 f"{items_after.dirs}")

            assert items_before.files == items_after.files, \
                f"different files detected - before {items_before.files} / after {items_after.files}"

            remaining_dirs = items_after.dirs.subtract(items_before.dirs)

            assert len(remaining_dirs) == 1, \
                f"more than one directories have changed: {remaining_dirs}"

            assert remaining_dirs[0] == new_copied_dir, \
                f"the name of the changed directory does not match: `{remaining_dirs[0]}` (expected `{new_copied_dir}`)"
        finally:
            self.Filesystem.dir_deleter.delete_directory(new_copied_dir)
