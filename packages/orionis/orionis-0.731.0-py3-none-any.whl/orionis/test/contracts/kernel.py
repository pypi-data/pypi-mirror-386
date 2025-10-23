from abc import ABC, abstractmethod
from orionis.test.contracts.unit_test import IUnitTest

class ITestKernel(ABC):
    """
    Interface for test kernel implementations in the Orionis testing framework.

    The test kernel manages the application context, validates and handles test configuration,
    orchestrates test discovery and execution, and provides a unified interface for test operations.
    """

    @abstractmethod
    def handle(
        self,
        modules: list = []
    ) -> IUnitTest:
        """
        Configures and executes unit tests based on the current test kernel configuration.

        This method sets up the test environment, loads the specified modules, and orchestrates
        the execution of unit tests. It returns an instance of `IUnitTest` representing the
        results and state of the executed tests.

        Parameters
        ----------
        modules : list, optional
            A list of modules to be included in the test execution. Defaults to an empty list.

        Returns
        -------
        IUnitTest
            An instance representing the configured and executed unit test.
        """
        pass
