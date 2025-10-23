from typing import Any, List
from orionis.console.contracts.cli_request import ICLIRequest
from orionis.console.exceptions import CLIOrionisValueError

class CLIRequest(ICLIRequest):

    @classmethod
    def fromList(cls, args: List[str]) -> 'CLIRequest': # NOSONAR
        """
        Create a CLIRequest instance from a list of command line arguments.

        This class method provides a convenient way to construct a CLIRequest object
        directly from a list of command line arguments, such as those typically
        received from sys.argv. It parses the arguments according to common CLI
        conventions and extracts the command name and associated parameters.

        Parameters
        ----------
        args : list
            A list of command line arguments where the first element is expected
            to be the command name, and subsequent elements are command arguments
            in the format '--key=value', '--flag', or 'value'. Empty lists are
            handled gracefully with fallback behavior.

        Returns
        -------
        CLIRequest
            A new CLIRequest instance initialized with the parsed command name
            and arguments dictionary extracted from the input list.

        Examples
        --------
        >>> args = ['migrate', '--database=production', '--force', 'users']
        >>> request = CLIRequest.fromList(args)
        >>> request.command()
        'migrate'
        >>> request.argument('database')
        'production'
        >>> request.argument('force')
        'force'

        Notes
        -----
        The parsing logic follows these conventions:
        - First argument is always treated as the command name
        - Arguments with '=' are split into key-value pairs
        - Arguments starting with '--' have the prefix removed
        - Flag arguments (--flag) are stored with the flag name as both key and value
        - Regular arguments without '=' are stored with the argument as both key and value
        - Empty or single-element lists result in default command names and empty arguments
        """

        # Validate that args is a list
        if not isinstance(args, list):
            raise CLIOrionisValueError(
                f"Failed to create CLIRequest from list: expected list, got {type(args).__module__}.{type(args).__name__}."
            )

        # Extract command name with defensive programming for edge cases
        # Use fallback command name for empty lists or malformed input
        command = args[0] if args and len(args) > 0 else "__unknown__"

        # Initialize command arguments dictionary for storing parsed parameters
        command_args = {}

        # Process command arguments if any exist beyond the command name
        if args and len(args) > 1:

            # Iterate over each argument provided after the command name
            for arg in args[1:]:

                # Handle arguments in key=value format
                if '=' in arg:

                    # Handle key=value format arguments
                    key, value = arg.split('=', 1)  # Split only on first '=' to preserve values with '='

                    # Normalize key by removing common CLI prefixes
                    if key.startswith('--'):
                        key = key[2:]  # Remove double-dash prefix

                    command_args[key] = value

                else:

                    # Handle flag-style arguments and standalone values
                    if arg.startswith('--'):

                        # Extract flag name by removing prefix and store as flag=flag
                        flag_name = arg[2:]
                        command_args[flag_name] = flag_name

                    else:

                        # For regular arguments without '=', store as arg=arg
                        command_args[arg] = arg

        # Create and return a new CLIRequest instance with parsed command and arguments
        return cls(command, command_args)

    def __init__(
        self,
        command: str = "__unknown__",
        args: dict = {}
    ):
        """
        Initialize a CLI request object with command line arguments.

        Args:
            args (dict, optional): Dictionary containing command line arguments and their values.
                                  Defaults to an empty dictionary.

        Raises:
            CLIOrionisValueError: If the provided args parameter is not a dictionary.

        Note:
            The args dictionary is stored privately and used to manage CLI request parameters
            throughout the lifecycle of the CLI request object.
        """

        # Validate that args is a dictionary
        if not isinstance(args, dict):
            raise CLIOrionisValueError("Args must be a dictionary")

        # Validate that command is a string
        if not isinstance(command, str):
            raise CLIOrionisValueError("Command must be a string")

        # Store the args dictionary as a private attribute
        self.__command = command
        self.__args = args if args is not None else {}

    def command(self) -> str:
        """
        Retrieve the command name associated with this CLI request.

        This method provides access to the command string that was specified during
        the initialization of the CLIRequest object. The command represents the
        primary action or operation that should be executed based on the CLI input.

        Returns
        -------
        str
            The command name stored as a string. This is the exact command value
            that was passed to the constructor during object initialization.

        Notes
        -----
        The returned command string is immutable and represents the core action
        identifier for this CLI request. This value is essential for determining
        which operation should be performed by the CLI handler.
        """

        # Return the command name stored in the private attribute
        # This provides access to the command specified during initialization
        return self.__command

    def arguments(self) -> dict:
        """
        Retrieve all command line arguments as a complete dictionary.

        This method provides access to the entire collection of command line arguments
        that were passed during the initialization of the CLIRequest object. It returns
        a reference to the internal arguments dictionary, allowing for comprehensive
        access to all parsed CLI parameters.

        Returns
        -------
        dict
            A dictionary containing all the parsed command line arguments as key-value
            pairs, where keys are argument names (str) and values are the corresponding
            argument values of any type. If no arguments were provided during
            initialization, returns an empty dictionary.

        Notes
        -----
        This method returns a reference to the internal arguments dictionary rather
        than a copy. Modifications to the returned dictionary will affect the
        internal state of the CLIRequest object.
        """

        # Return the complete arguments dictionary containing all CLI parameters
        return self.__args

    def argument(self, name: str, default: Any = None):
        """
        Retrieve the value of a specific command line argument by its name.

        This method provides access to individual command line arguments that were
        passed during initialization. It safely retrieves argument values without
        raising exceptions if the argument doesn't exist.

        Parameters
        ----------
        name : str
            The name of the command line argument to retrieve. This should match
            the key used when the argument was originally parsed and stored.
        default : Any, optional
            The default value to return if the specified argument name does not
            exist in the arguments dictionary. Defaults to None.

        Returns
        -------
        Any or None
            The value associated with the specified argument name if it exists
            in the arguments dictionary. Returns None if the argument name is
            not found or was not provided during CLI execution.

        Notes
        -----
        This method uses the dictionary's get() method to safely access values,
        ensuring that missing arguments return None rather than raising a KeyError.
        """

        # Safely retrieve the argument value using dict.get() to avoid KeyError
        # Returns None if the argument name doesn't exist in the dictionary
        if name not in self.__args or self.__args[name] is None:
            return default

        # Return the value associated with the specified argument name
        return self.__args.get(name, default)