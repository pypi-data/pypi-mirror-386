import pathlib
import balder

from balderhub.fileops.lib.scenario_features import FileSystemNavigatorFeature


class AbstractScenarioBase(balder.Scenario):
    """
    Abstract scenario class that is shared for almost all scenarios within this project
    """
    #: this is the directory within this scenario should execute its tests
    EXECUTE_IN_DIR = pathlib.Path('/')

    class Filesystem(balder.Device):
        """
        The main device that has the filesystem by itself or allows to control it
        """
        navigator = FileSystemNavigatorFeature()
