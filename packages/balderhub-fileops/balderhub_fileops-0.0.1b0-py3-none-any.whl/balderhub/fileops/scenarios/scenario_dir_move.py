import balder

from balderhub.fileops.scenarios.abstract_scenario_base import AbstractScenarioBase
from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature, DirectoryCreatorFeature, \
    DirectoryMoverFeature, DirectoryDeleterFeature
from balderhub.fileops.lib.utils import DirectoryItem


class ScenarioDirMoveStandalone(AbstractScenarioBase):
    """
    Standalone scenario that provides test for MOVING directories.

    This standalone version also creates a test directory to move and cleans up everything afterward.
    """

    class Filesystem(AbstractScenarioBase.Filesystem):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
        dir_creator = DirectoryCreatorFeature()  # TODO another scenario with already provided dirs??
        dir_deleter = DirectoryDeleterFeature()  # TODO another scenario with already provided dirs??
        dir_mover = DirectoryMoverFeature()

    @balder.fixture('testcase')
    def dir_to_move(self):
        """fixture that creates and cleans up a test directory"""
        directory = DirectoryItem('dir_to_move')
        self.Filesystem.dir_creator.create_new_directory(directory.name)

        yield directory

        if directory in self.Filesystem.navigator.get_all_list_items():
            self.Filesystem.dir_deleter.delete_directory(directory)

    @balder.fixture('testcase')
    def destination_dir(self):
        """fixture that creates and cleans up a test directory to move directories in"""
        destination_dir = DirectoryItem('destination_dir')
        self.Filesystem.dir_creator.create_new_directory(destination_dir.name)

        yield destination_dir

        self.Filesystem.dir_deleter.delete_directory(destination_dir)

    def test_move_directory(self, dir_to_move: DirectoryItem, destination_dir: DirectoryItem):
        """
        Simple test that tries to move the test directory to the destination directory. It will automatically clean up
        everything it changed afterward.
        """
        items_before = self.Filesystem.navigator.get_all_list_items()
        assert dir_to_move in items_before

        assert destination_dir in items_before, f"can not find {destination_dir} in current elements {items_before}"
        assert dir_to_move in items_before, f"can not find {dir_to_move} in current elements {items_before}"

        # go into destination dir and check content there
        try:
            self.Filesystem.navigator.navigate_to(self.EXECUTE_IN_DIR.joinpath(destination_dir.name))
            elements_within_destination_before = self.Filesystem.navigator.get_all_list_items()
            assert dir_to_move not in elements_within_destination_before, \
                f"found another {dir_to_move} within the destionation {destination_dir}"
        finally:
            self.Filesystem.navigator.navigate_to(self.EXECUTE_IN_DIR)

        # now move the first directory
        self.Filesystem.dir_mover.move_directory(dir_to_move, destination_dir)

        items_after = self.Filesystem.navigator.get_all_list_items()

        assert items_before.files == items_after.files, \
            f"different files detected - before {items_before.files} / after {items_after.files}"

        assert len(items_before.dirs) == len(items_after.dirs) + 1, \
            (f"detect unexpected number of directories: {len(items_after.dirs)} (expected {len(items_before.dirs) + 1})"
             f" - before: {items_before.dirs} | after: {items_after.dirs}")

        assert dir_to_move not in items_after, f"{dir_to_move} should not be available in {items_after}"

        # make sure that content of `dir_to_move` is in `new_moved_dir`
        try:
            self.Filesystem.navigator.navigate_to(self.EXECUTE_IN_DIR.joinpath(destination_dir.name))
            elements_within_destination_after = self.Filesystem.navigator.get_all_list_items()
            assert dir_to_move in elements_within_destination_after, \
                f"found another {dir_to_move} within the destionation {destination_dir}"

            new_elements_in_dest_dir = elements_within_destination_after.subtract(elements_within_destination_before)

            assert len(new_elements_in_dest_dir) == 1, \
                f"detect unexpected number of elements in destination {destination_dir}: {new_elements_in_dest_dir}"
            assert new_elements_in_dest_dir[0] == dir_to_move, \
                (f"detect unexpected directory - expected that new directory is {dir_to_move}, but in reality it is "
                 f"{new_elements_in_dest_dir[0]}")

        finally:
            self.Filesystem.navigator.navigate_to(self.EXECUTE_IN_DIR)
