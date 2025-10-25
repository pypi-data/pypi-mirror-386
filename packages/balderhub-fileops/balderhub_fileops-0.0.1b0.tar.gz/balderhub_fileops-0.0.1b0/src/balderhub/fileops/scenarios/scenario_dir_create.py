import balder

from balderhub.fileops.scenarios.abstract_scenario_base import AbstractScenarioBase
from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature, DirectoryCreatorFeature, \
    DirectoryDeleterFeature
from balderhub.fileops.lib.utils import DirectoryItem


class ScenarioDirCreateStandalone(AbstractScenarioBase):
    """
    Standalone scenario that provides test for CREATING directories.

    This standalone version also cleans up everything afterward.
    """

    class Filesystem(AbstractScenarioBase.Filesystem):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
        dir_creator = DirectoryCreatorFeature()
        dir_deleter = DirectoryDeleterFeature()  # TODO another scenario with already provided dirs??


    @balder.fixture('testcase')
    def dir_to_create(self):
        """fixture that creates and cleans up a test directory"""
        directory = DirectoryItem('dir_to_create')
        return directory

    def test_create_new_valid_dir(self, dir_to_create):
        """
        Simple test that tries to create a test directory. It will automatically clean up everything it changed
        afterward.
        """
        self.Filesystem.navigator.navigate_to(self.EXECUTE_IN_DIR)

        items_before = self.Filesystem.navigator.get_all_list_items()

        assert dir_to_create not in items_before, f"the {dir_to_create} already exists - can not create it again"

        try:
            self.Filesystem.dir_creator.create_new_directory(dir_to_create.name)
            items_after = self.Filesystem.navigator.get_all_list_items()

            assert items_before.files.compare_with(items_after.files), \
                f"different files detected - before {items_before.files} / after {items_after.files}"

            assert len(items_after.dirs) == len(items_before.dirs) + 1, \
                (f"detect unexpected number of directories: {len(items_after.dirs)} "
                 f"(expected {len(items_before.dirs) + 1}) - "
                 f"before: {items_before.dirs} | after: {items_after.dirs}")

            new_items = items_after.subtract(items_before)

            assert len(new_items) == 1, \
                f"detect unexpected number of added directories: {new_items} (expected only `{dir_to_create}`)"
            assert new_items[0] == dir_to_create, \
                f"detect unexpected directory: {new_items[0]} (expected {dir_to_create})"
            # TODO also check the content

        finally:
            self.Filesystem.dir_deleter.delete_directory(dir_to_create)
