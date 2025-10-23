from orionis.test.exceptions import OrionisTestValueError

class __ValidPrintResult:

    def __call__(self, print_result) -> bool:
        """
        Validates that the input is a boolean value.

        Parameters
        ----------
        print_result : Any
            The value to be validated as a boolean.

        Returns
        -------
        bool
            The validated boolean value.

        Raises
        ------
        OrionisTestValueError
            If `print_result` is not of type `bool`.
        """
        if not isinstance(print_result, bool):
            raise OrionisTestValueError(
                f"Invalid print_result: Expected a boolean, got '{print_result}' ({type(print_result).__name__})."
            )

        return print_result

# Exported singleton instance
ValidPrintResult = __ValidPrintResult()