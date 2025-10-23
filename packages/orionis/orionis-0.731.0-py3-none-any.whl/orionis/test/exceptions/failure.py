import unittest

class OrionisTestFailureException(Exception):

    def __init__(self, result: unittest.TestResult):
        """
        Initialize the exception with details of failed and errored tests.

        Parameters
        ----------
        result : unittest.TestResult
            The test result object containing information about test failures and errors.

        Attributes
        ----------
        failed_tests : list of str
            List of test IDs that failed.
        errored_tests : list of str
            List of test IDs that encountered errors.
        error_messages : list of str
            List of formatted error messages for each failed or errored test.
        text : str
            Formatted string summarizing all test failures and errors.
        """
        # Collect IDs of failed tests
        failed_tests = [test.id() for test, _ in result.failures]

        # Collect IDs of tests that encountered errors
        errored_tests = [test.id() for test, _ in result.errors]

        error_messages = []

        # Add formatted messages for failed tests
        for test in failed_tests:
            error_messages.append(f"Test Fail: {test}")

        # Add formatted messages for errored tests
        for test in errored_tests:
            error_messages.append(f"Test Error: {test}")

        # Combine all error messages into a single string
        text = "\n".join(error_messages)

        # Initialize the base Exception with the summary message
        super().__init__(f"{len(failed_tests) + len(errored_tests)} test(s) failed or errored:\n{text}")

    def __str__(self) -> str:
        """
        Return a formatted string describing the exception.

        Returns
        -------
        str
            The summary message containing the number and details of failed and errored tests.
        """
        # Return the first argument passed to the exception as a string
        return str(self.args[0])
