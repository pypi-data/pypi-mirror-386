import argparse
import os
from pathlib import Path
import re
from typing import Any, List, Optional
from orionis.console.args.argument import CLIArgument
from orionis.console.base.command import BaseCommand
from orionis.console.contracts.base_command import IBaseCommand
from orionis.console.contracts.cli_request import ICLIRequest
from orionis.console.contracts.command import ICommand
from orionis.console.contracts.reactor import IReactor
from orionis.console.entities.command import Command
from orionis.console.exceptions import CLIOrionisValueError, CLIOrionisRuntimeError
from orionis.console.contracts.executor import IExecutor
from orionis.console.exceptions import CLIOrionisTypeError
from orionis.console.request.cli_request import CLIRequest
from orionis.foundation.contracts.application import IApplication
from orionis.services.introspection.concretes.reflection import ReflectionConcrete
from orionis.services.introspection.instances.reflection import ReflectionInstance
from orionis.services.introspection.modules.reflection import ReflectionModule
from orionis.services.log.contracts.log_service import ILogger
from orionis.support.performance.contracts.counter import IPerformanceCounter

class Reactor(IReactor):

    def __init__(
        self,
        app: IApplication
    ):
        """
        Initializes a new Reactor instance for command discovery and management.

        The Reactor constructor sets up the command processing environment by establishing
        the application context, determining the project root directory, and automatically
        discovering and loading command classes from the console commands directory.
        It maintains an internal registry of discovered commands for efficient lookup
        and execution.

        Parameters
        ----------
        app : Optional[IApplication], default None
            The application instance to use for command processing. If None is provided,
            a new Orionis application instance will be created automatically. The
            application instance provides access to configuration, paths, and other
            framework services required for command execution.

        Returns
        -------
        None
            This is a constructor method and does not return any value. The instance
            is configured with the provided or default application and populated with
            discovered commands.

        Notes
        -----
        - Command discovery is performed automatically during initialization
        - The current working directory is used as the project root for module resolution
        - Commands are loaded from the path specified by app.path('commands')
        - The internal command registry is initialized as an empty dictionary before loading
        """

        # Initialize the application instance, using provided app or creating new Orionis instance
        self.__app = app

        # Initialize the internal command registry as an empty dictionary
        self.__commands: dict[str, Command] = {}

        # Initialize the executor for command output management
        self.__executer: IExecutor = self.__app.make(IExecutor)

        # Initialize the logger service for logging command execution details
        self.__logger: ILogger = self.__app.make(ILogger)

        # Initialize the performance counter for measuring command execution time
        self.__performance_counter: IPerformanceCounter = self.__app.make(IPerformanceCounter)

        # List to hold fluent command definitions
        self.__fluent_commands: List[ICommand] = []

    def __loadCommands(self) -> None:
        """
        Loads all available commands into the reactor's internal registry.

        This method ensures that all commands—custom user-defined, core framework, and fluent interface
        commands—are loaded and registered in the reactor's internal command registry. It uses internal
        flags to prevent duplicate loading and to optimize performance by ensuring each command set is
        loaded only once per reactor instance.

        The loading order is as follows:
            1. Core commands (if not already loaded)
            2. Custom user-defined commands (if not already loaded)
            3. Fluent interface commands (if not already loaded)

        This order allows custom commands to override core commands if they share the same signature,
        and ensures that all available commands are discoverable and executable.

        Parameters
        ----------
        None

        Returns
        -------
        None
            This method does not return any value. All discovered commands are registered
            internally in the reactor's command registry and become available for execution.

        Notes
        -----
        - Each command set is loaded only once per reactor instance.
        - The internal flags `__load__core_commands`, `__load__custom_commands`, and
          `__load_fluent_commands` track the loading state of each command set.
        - Both loading methods handle their own error handling and validation.
        """

        # Load core commands if they have not been loaded yet
        if not hasattr(self, '_Reactor__load__core_commands') or not self.__load__core_commands:
            self.__loadCoreCommands()
            self.__load__core_commands = True

        # Load custom user-defined commands if they have not been loaded yet
        if not hasattr(self, '_Reactor__load__custom_commands') or not self.__load__custom_commands:
            self.__loadCustomCommands()
            self.__load__custom_commands = True

        # Load fluent interface commands if they have not been loaded yet
        if not hasattr(self, '_Reactor__load_fluent_commands') or not self.__load_fluent_commands:
            self.__loadFluentCommands()
            self.__load_fluent_commands = True

    def __loadFluentCommands(self) -> None: # NOSONAR
        """
        Loads and registers commands defined using the fluent interface.

        This method iterates through all commands that have been defined using the
        fluent interface pattern and registers them in the reactor's internal command
        registry. Each fluent command is validated for structure and metadata before
        being added to ensure proper integration and discoverability.

        Returns
        -------
        None
            This method does not return any value. All fluent commands are
            registered internally in the reactor's command registry for later lookup
            and execution.
        """

        # Import library for dynamic module importing
        import importlib

        # Get the routes directory path from the application instance
        routes_path = self.__app.path('routes')

        # Check if routes directory exists
        if not os.path.exists(routes_path):
            return

        # Get the project root directory for module path resolution
        root_path = str(self.__app.path('root'))

        # List all .py files in the routes directory and subdirectories
        for current_directory, _, files in os.walk(routes_path):

            # Iterate through each file in the current directory
            for file in files:

                # Only process Python files
                if file.endswith('.py'):

                    # Construct the full file path
                    file_path = os.path.join(current_directory, file)

                    # Read file content to check for Reactor.command usage
                    try:

                        # Open and read the file content
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Check if the file contains a Reactor.command definition
                        if 'from orionis.support.facades.reactor import Reactor' in content:

                            # Sanitize the module path for import
                            pre_module = current_directory.replace(root_path, '')\
                                                          .replace(os.sep, '.')\
                                                          .lstrip('.')

                            # Remove virtual environment paths
                            pre_module = re.sub(r'[^.]*\.(?:Lib|lib)\.(?:python[^.]*\.)?site-packages\.?', '', pre_module)
                            pre_module = re.sub(r'\.?v?env\.?', '', pre_module)
                            pre_module = re.sub(r'\.+', '.', pre_module).strip('.')

                            # Skip if module name is empty after cleaning
                            if not pre_module:
                                continue

                            # Create the reflection module path
                            module_name = f"{pre_module}.{file[:-3]}"

                            try:

                                # Import the module natively using importlib
                                importlib.import_module(module_name)

                            except Exception as e:

                                # Raise a runtime error if module import fails
                                raise CLIOrionisRuntimeError(
                                    f"Failed to import module '{module_name}' from file '{file_path}': {e}"
                                ) from e

                    except Exception as e:

                        # Raise a runtime error if file reading fails
                        raise CLIOrionisRuntimeError(
                            f"Failed to read file '{file_path}' for fluent command loading: {e}"
                        ) from e

        # Import Command entity here to avoid circular imports
        from orionis.console.entities.command import Command as CommandEntity

        # Iterate through all fluent command definitions
        for f_command in self.__fluent_commands:

            # If the fluent command has a get method, retrieve its signature and command entity
            if hasattr(f_command, 'get') and callable(getattr(f_command, 'get')):

                # Get the signature and command entity from the fluent command
                values = f_command.get()
                signature: str = values[0]
                command_entity: CommandEntity = values[1]

                # Build the arguments dictionary from the CLIArgument instances
                required_args: List[CLIArgument] = command_entity.args

                # Create an ArgumentParser instance to handle the command arguments
                arg_parser = argparse.ArgumentParser(
                    usage=f"python -B reactor {signature} [options]",
                    description=f"Command [{signature}] : {command_entity.description}",
                    formatter_class=argparse.RawTextHelpFormatter,
                    add_help=True,
                    allow_abbrev=False,
                    exit_on_error=True,
                    prog=signature
                )

                # Iterate through each CLIArgument and add it to the ArgumentParser
                for arg in required_args:
                    arg.addToParser(arg_parser)

                # Register the command in the internal registry with all its metadata
                self.__commands[signature] = Command(
                    obj=command_entity.obj,
                    method=command_entity.method,
                    timestamps=command_entity.timestamps,
                    signature=signature,
                    description=command_entity.description,
                    args=arg_parser
                )

    def __loadCoreCommands(self) -> None:
        """
        Loads and registers core command classes provided by the Orionis framework.

        This method is responsible for discovering and registering core command classes
        that are bundled with the Orionis framework itself (such as version, help, etc.).
        These commands are essential for the framework's operation and are made available
        to the command registry so they can be executed like any other user-defined command.

        The method imports the required core command classes, validates their structure,
        and registers them in the internal command registry. Each command is checked for
        required attributes such as `timestamps`, `signature`, `description`, and `arguments`
        to ensure proper integration and discoverability.

        Returns
        -------
        None
            This method does not return any value. All discovered core commands are
            registered internally in the reactor's command registry for later lookup
            and execution.
        """

        # Import the core command class for version
        from orionis.console.commands.__publisher__ import PublisherCommand
        from orionis.console.commands.cache_clear import CacheClearCommand
        from orionis.console.commands.help import HelpCommand
        from orionis.console.commands.log_clear import LogClearCommand
        from orionis.console.commands.make_command import MakeCommand
        from orionis.console.commands.scheduler_list import ScheduleListCommand
        from orionis.console.commands.scheduler_work import ScheduleWorkCommand
        from orionis.console.commands.test import TestCommand
        from orionis.console.commands.version import VersionCommand

        # List of core command classes to load (extend this list as more core commands are added)
        core_commands = [
            PublisherCommand,
            CacheClearCommand,
            HelpCommand,
            LogClearCommand,
            MakeCommand,
            ScheduleListCommand,
            ScheduleWorkCommand,
            TestCommand,
            VersionCommand
        ]

        # Iterate through the core command classes and register them
        for obj in core_commands:

            # Get the signature attribute from the command class
            signature = ReflectionConcrete(obj).getAttribute('signature')

            # Skip if signature is not defined
            if signature is None:
                continue

            # Validate and extract required command attributes
            timestamp = self.__ensureTimestamps(obj)
            description = self.__ensureDescription(obj)
            args = self.__ensureArguments(obj)

            # Register the command in the internal registry with all its metadata
            self.__commands[signature] = Command(
                obj=obj,
                method='handle',
                timestamps=timestamp,
                signature=signature,
                description=description,
                args=args
            )

    def __loadCustomCommands(self) -> None: # NOSONAR
        """
        Loads command classes from Python files in the specified commands directory.

        This method recursively walks through the commands directory, imports Python modules,
        and registers command classes that inherit from BaseCommand. It performs module path
        sanitization to handle virtual environment paths and validates command structure
        before registration.

        Returns
        -------
        None
            This method does not return any value. Command classes are registered
            internally in the reactor's command registry.

        Notes
        -----
        - Only Python files (.py extension) are processed
        - Virtual environment paths are automatically filtered out during module resolution
        - Command classes must inherit from BaseCommand to be registered
        - Each discovered command class undergoes structure validation via __ensureStructure
        """

        # Ensure the provided commands_path is a valid directory
        commands_path = (Path(self.__app.path('console')) / 'commands').resolve()
        root_path = str(self.__app.path('root'))

        # Iterate through the command path and load command modules
        for current_directory, _, files in os.walk(commands_path):

            # Iterate through each file in the current directory
            for file in files:

                # Only process Python files
                if file.endswith('.py'):

                    # Sanitize the module path by converting filesystem path to Python module notation
                    pre_module = current_directory.replace(root_path, '')\
                                                  .replace(os.sep, '.')\
                                                  .lstrip('.')

                    # Remove virtual environment paths using regex (Windows, Linux, macOS)
                    # Windows: venv\Lib\site-packages or venv\lib\site-packages
                    # Linux/macOS: venv/lib/python*/site-packages
                    pre_module = re.sub(r'[^.]*\.(?:Lib|lib)\.(?:python[^.]*\.)?site-packages\.?', '', pre_module)

                    # Remove any remaining .venv or venv patterns from the module path
                    pre_module = re.sub(r'\.?v?env\.?', '', pre_module)

                    # Clean up any double dots or leading/trailing dots that may have been created
                    pre_module = re.sub(r'\.+', '.', pre_module).strip('.')

                    # Skip if module name is empty after cleaning (invalid module path)
                    if not pre_module:
                        continue

                    # Create the reflection module path by combining sanitized path with filename
                    rf_module = ReflectionModule(f"{pre_module}.{file[:-3]}")

                    # Iterate through all classes found in the current module
                    for name, obj in rf_module.getClasses().items():

                        # Check if the class is a valid command class (inherits from BaseCommand but is not BaseCommand itself)
                        if issubclass(obj, BaseCommand) and obj is not BaseCommand and obj is not IBaseCommand:

                            # Validate the command class structure and register it
                            timestamp = self.__ensureTimestamps(obj)
                            signature = self.__ensureSignature(obj)
                            description = self.__ensureDescription(obj)
                            args = self.__ensureArguments(obj)

                            # Add the command to the internal registry
                            self.__commands[signature] = Command(
                                obj=obj,
                                method='handle',
                                timestamps=timestamp,
                                signature=signature,
                                description=description,
                                args=args
                            )

    def __ensureTimestamps(self, obj: IBaseCommand) -> bool:
        """
        Validates that a command class has a properly formatted timestamps attribute.

        This method ensures that the command class contains a 'timestamps' attribute
        that is a boolean value, indicating whether timestamps should be included in
        console output messages.

        Parameters
        ----------
        obj : IBaseCommand
            The command class instance to validate.

        Returns
        -------
        Reactor
            Returns self to enable method chaining for additional validation calls.

        Raises
        ------
        ValueError
            If the command class lacks a 'timestamps' attribute or if the attribute is not a boolean.
        """

        # Check if the command class has a timestamps attribute
        if not hasattr(obj, 'timestamps'):
            return False

        # Ensure the timestamps attribute is a boolean type
        if not isinstance(obj.timestamps, bool):
            raise CLIOrionisTypeError(f"Command class {obj.__name__} 'timestamps' must be a boolean.")

        # Return timestamps value
        return obj.timestamps

    def __ensureSignature(self, obj: IBaseCommand) -> str:
        """
        Validates that a command class has a properly formatted signature attribute.

        This method ensures that the command class contains a 'signature' attribute
        that follows the required naming conventions for command identification.
        The signature must be a non-empty string containing only alphanumeric
        characters, underscores, and colons, with specific placement rules.

        Parameters
        ----------
        obj : IBaseCommand
            The command class instance to validate.

        Returns
        -------
        Reactor
            Returns self to enable method chaining.

        Raises
        ------
        CLIOrionisValueError
            If the command class lacks a 'signature' attribute, if the signature
            is an empty string, or if the signature doesn't match the required pattern.
        CLIOrionisTypeError
            If the 'signature' attribute is not a string.
        """

        # Check if the command class has a signature attribute
        if not hasattr(obj, 'signature'):
            raise CLIOrionisValueError(f"Command class {obj.__name__} must have a 'signature' attribute.")

        # Ensure the signature attribute is a string type
        if not isinstance(obj.signature, str):
            raise CLIOrionisTypeError(f"Command class {obj.__name__} 'signature' must be a string.")

        # Validate that the signature is not empty after stripping whitespace
        if obj.signature.strip() == '':
            raise CLIOrionisValueError(f"Command class {obj.__name__} 'signature' cannot be an empty string.")

        # Define the regex pattern for valid signature format
        # Pattern allows: alphanumeric chars, underscores, colons
        # Cannot start/end with underscore or colon, cannot start with number
        pattern = r'^[a-zA-Z][a-zA-Z0-9_:]*[a-zA-Z0-9]$|^[a-zA-Z]$'

        # Validate the signature against the required pattern
        if not re.match(pattern, obj.signature):
            raise CLIOrionisValueError(
                f"Command class {obj.__name__} 'signature' must contain only alphanumeric characters, underscores (_) and colons (:), cannot start or end with underscore or colon, and cannot start with a number."
            )

        # Return signature
        return obj.signature.strip()

    def __ensureDescription(self, obj: IBaseCommand) -> str:
        """
        Validates that a command class has a properly formatted description attribute.

        This method ensures that the command class contains a 'description' attribute
        that provides meaningful documentation for the command. The description must
        be a non-empty string that can be used for help documentation and command
        listing purposes.

        Parameters
        ----------
        obj : IBaseCommand
            The command class instance to validate.

        Returns
        -------
        Reactor
            Returns self to enable method chaining for additional validation calls.

        Raises
        ------
        CLIOrionisValueError
            If the command class lacks a 'description' attribute or if the description
            is an empty string after stripping whitespace.
        CLIOrionisTypeError
            If the 'description' attribute is not a string type.
        """

        # Check if the command class has a description attribute
        if not hasattr(obj, 'description'):
            raise CLIOrionisValueError(f"Command class {obj.__name__} must have a 'description' attribute.")

        # Ensure the description attribute is a string type
        if not isinstance(obj.description, str):
            raise CLIOrionisTypeError(f"Command class {obj.__name__} 'description' must be a string.")

        # Validate that the description is not empty after stripping whitespace
        if obj.description.strip() == '':
            raise CLIOrionisValueError(f"Command class {obj.__name__} 'description' cannot be an empty string.")

        # Return description
        return obj.description.strip()

    def __ensureArguments(self, obj: IBaseCommand) -> Optional[argparse.ArgumentParser]:
        """
        Validates and processes command arguments for a command class.

        Ensures the command class provides a valid list of CLIArgument instances via its 'options' method,
        and constructs an ArgumentParser accordingly.

        Parameters
        ----------
        obj : IBaseCommand
            The command class instance to validate.

        Returns
        -------
        Optional[argparse.ArgumentParser]
            An ArgumentParser instance configured with the command's arguments,
            or None if the command has no arguments.

        Raises
        ------
        CLIOrionisTypeError
            If the 'options' method does not return a list or contains non-CLIArgument instances.
        """

        try:

            # Instantiate the command and retrieve its options
            instance = self.__app.make(obj)
            options: List[CLIArgument]  = self.__app.call(instance, 'options')

            # Validate that options is a list
            if not isinstance(options, list):
                raise CLIOrionisTypeError(
                    f"Command class {obj.__name__} 'options' must return a list."
                )

            # Return None if there are no arguments
            if not options:
                return None

            # Validate all items are CLIArgument instances
            for idx, arg in enumerate(options):
                if not isinstance(arg, CLIArgument):
                    raise CLIOrionisTypeError(
                        f"Command class {obj.__name__} 'options' must contain only CLIArgument instances, "
                        f"found '{type(arg).__name__}' at index {idx}."
                    )


            # Get the Signature attribute from the command class
            rf_concrete = ReflectionConcrete(obj)
            signature = rf_concrete.getAttribute('signature', '<unknown>')
            description = rf_concrete.getAttribute('description', '')

            # Build the ArgumentParser
            arg_parser = argparse.ArgumentParser(
                usage=f"python -B reactor {signature} [options]",
                description=f"Command [{signature}] : {description}",
                formatter_class=argparse.RawTextHelpFormatter,
                add_help=True,
                allow_abbrev=False,
                exit_on_error=True,
                prog=signature
            )

            # Add each CLIArgument to the ArgumentParser
            for arg in options:
                arg.addToParser(arg_parser)

            # Return the constructed ArgumentParser
            return arg_parser

        except Exception as e:

            # Raise a runtime error if any exception occurs during argument processing
            raise CLIOrionisRuntimeError(e) from e

    def __parseArgs(
        self,
        command: Command,
        args: Optional[List[str]] = None
    ) -> dict:
        """
        Parses command-line arguments for a given command using its internal ArgumentParser.

        This method takes a command object and an optional list of command-line arguments,
        and parses them into a dictionary of argument names and values. If the command
        defines an ArgumentParser (i.e., expects arguments), the arguments are parsed
        accordingly. If no arguments are expected or provided, an empty dictionary is returned.

        Parameters
        ----------
        command : Command
            The command object containing the argument parser and metadata.
        args : Optional[List[str]], default None
            A list of command-line arguments to parse. If None, an empty list is used.

        Returns
        -------
        dict
            A dictionary containing the parsed argument names and their corresponding values.
            Returns an empty dictionary if no arguments are expected or provided.

        Raises
        ------
        SystemExit
            Raised by argparse if argument parsing fails or if help is requested.
        """

        # Initialize parsed_args to None
        parsed_args = None

        # If the command expects arguments, parse them using its ArgumentParser
        if command.args is not None and isinstance(command.args, argparse.ArgumentParser):

            # If no args provided, use an empty list
            if args is None:
                args = []

            # Parse the provided arguments using the command's ArgumentParser
            try:
                parsed_args = command.args.parse_args(args)

            # Raise a CLIOrionisRuntimeError with the help message included in the exception
            except Exception:
                raise CLIOrionisRuntimeError(
                    f"Failed to parse arguments for command '{command.signature}'.\n"
                    f"{command.args.format_help()}\n"
                    "Please check the command syntax and available options."
                )

        # Convert the parsed arguments to a dictionary and return
        if isinstance(parsed_args, argparse.Namespace):
            return vars(parsed_args)

        # If parsed_args is already a dictionary, return it directly
        elif isinstance(parsed_args, dict):
            return parsed_args

        # Return an empty dictionary if no arguments were parsed
        else:
            return {}

    def command(
        self,
        signature: str,
        handler: List[Any]
    ) -> ICommand:
        """
        Define a new command using a fluent interface.

        This method allows defining a new command with a specified signature and handler
        function using a fluent interface pattern. The command can be further configured
        by chaining additional method calls to set properties such as timestamps,
        description, and arguments.

        Parameters
        ----------
        signature : str
            The unique signature identifier for the command. Must follow naming conventions
            (alphanumeric characters, underscores, colons, cannot start/end with underscore
            or colon, cannot start with a number).
        handler : List[Any]
            A list containing the class and optionally the method name. The first element
            should be a class, and the second element (if provided) should be a string
            representing the method name.

        Returns
        -------
        ICommand
            Returns an instance of ICommand that allows further configuration of the command
            through method chaining.

        Raises
        ------
        CLIOrionisTypeError
            If the signature is not a string or if the handler is not a valid list.
        ValueError
            If the signature does not meet the required naming conventions.
        """

        # Import the FluentCommand class here to avoid circular imports
        from orionis.console.fluent.command import Command as FluentCommand

        # Validate the handler parameter
        if len(handler) < 1 or not isinstance(handler, list):
            raise CLIOrionisValueError("Handler must be a list with at least one element (the callable).")

        # Ensure the first element is a class
        if not hasattr(handler[0], '__call__') or not hasattr(handler[0], '__name__'):
            raise CLIOrionisTypeError("The first element of handler must be a class.")

        # Create a new FluentCommand instance with the provided signature and handler
        f_command = FluentCommand(
            signature=signature,
            concrete=handler[0],
            method=handler[1] if len(handler) > 1 else 'handle'
        )

        # Append the new command to the internal list of fluent commands
        self.__fluent_commands.append(f_command)

        # Return the newly created command for further configuration
        return self.__fluent_commands[-1]

    def info(self) -> List[dict]:
        """
        Retrieves a list of all registered commands with their metadata.

        This method returns a list of dictionaries, each containing information about
        a registered command, including its signature, description, and whether it has
        timestamps enabled. This is useful for introspection and displaying available
        commands to the user.

        Returns
        -------
        List[dict]
            A list of dictionaries representing the registered commands, where each dictionary
            contains the command's signature, description, and timestamps status.
        """

        # Ensure commands are loaded before retrieving information
        self.__loadCommands()

        # Prepare a list to hold command information
        commands_info = []

        # Iterate through all registered commands in the internal registry
        for command in self.__commands.values():

            # Extract command metadata
            signature:str = command.signature
            description:str = command.description

            # Skip internal commands (those with double underscores)
            if signature.startswith('__') and signature.endswith('__'):
                continue

            # Append command information to the list
            commands_info.append({
                "signature": signature,
                "description": description
            })

        # Return the sorted list of command information by signature
        return sorted(commands_info, key=lambda x: x['signature'])

    def call(
        self,
        signature: str,
        args: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        Executes a registered command synchronously by its signature, optionally passing command-line arguments.

        This method retrieves a command from the internal registry using its unique signature,
        validates and parses any provided arguments using the command's argument parser,
        and then executes the command's `handle` method synchronously. It manages execution timing,
        logging, and error handling, and returns any output produced by the command.

        Parameters
        ----------
        signature : str
            The unique signature identifier of the command to execute.
        args : Optional[List[str]], default None
            List of command-line arguments to pass to the command. If None, no arguments are provided.

        Returns
        -------
        Optional[Any]
            The output produced by the command's `handle` method if execution is successful.
            Returns None if the command does not produce a result or if an error occurs.

        Raises
        ------
        CLIOrionisValueError
            If the command with the specified signature is not found in the registry.
        SystemExit
            If argument parsing fails due to invalid arguments provided (raised by argparse).
        Exception
            Propagates any exception raised during command execution after logging and error output.

        Notes
        -----
        - Logs execution start, completion, and errors with timestamps if enabled.
        - Handles argument parsing and injects parsed arguments into the command instance.
        - All exceptions are logged and displayed in the console.
        """

        # Scope Request instances to this command execution context
        with self.__app.createContext():

            # Ensure commands are loaded before attempting to execute
            self.__loadCommands()

            # Retrieve the command from the registry by its signature
            command: Command = self.__commands.get(signature)
            if command is None:
                raise CLIOrionisValueError(f"Command '{signature}' not found.")

            # Start execution timer for performance measurement
            self.__performance_counter.start()

            # Log the command execution start with RUNNING state if timestamps are enabled
            if command.timestamps:
                self.__executer.running(program=signature)

            try:
                # Instantiate the command class using the application container
                command_instance: IBaseCommand = self.__app.make(command.obj)

                # Inject parsed arguments into the command instance
                dict_args = self.__parseArgs(command, args)

                # Only set arguments if the command instance has a setArguments method
                if ReflectionInstance(command_instance).hasMethod('setArguments'):
                    command_instance.setArguments(dict_args.copy())

                # Inject a scoped CLIRequest instance into the application container for the command's context
                self.__app.scopedInstance(ICLIRequest, CLIRequest(
                    command=signature,
                    args=dict_args.copy()
                ))

                # Execute the command's handle method and capture its output
                output = self.__app.call(command_instance, command.method)

                # Calculate elapsed time and log completion with DONE state if command.timestamps are enabled
                self.__performance_counter.stop()
                elapsed_time = round(self.__performance_counter.getSeconds(), 2)
                if command.timestamps:
                    self.__executer.done(program=signature, time=f"{elapsed_time}s")

                # Log successful execution in the logger service
                self.__logger.info(f"Command '{signature}' executed successfully in ({elapsed_time}) seconds.")

                # Return the output produced by the command, if any
                return output

            except Exception as e:

                # Log the error in the logger service
                self.__logger.error(f"Command '{signature}' execution failed: {e}")

                # Calculate elapsed time and log failure with ERROR state if command.timestamps are enabled
                self.__performance_counter.stop()
                elapsed_time = round(self.__performance_counter.getSeconds(), 2)
                if command.timestamps:
                    self.__executer.fail(program=signature, time=f"{elapsed_time}s")

                # Propagate the exception after logging
                raise

    async def callAsync(
        self,
        signature: str,
        args: Optional[List[str]] = None
    ) -> Optional[Any]:
        """
        Executes a registered command asynchronously by its signature, optionally passing command-line arguments.

        This method locates a command in the internal registry using its unique signature,
        validates and parses any provided arguments using the command's argument parser,
        and then executes the command's `handle` method asynchronously. It manages execution timing,
        logging, and error handling, and returns any output produced by the command.

        Parameters
        ----------
        signature : str
            The unique signature identifier of the command to execute.
        args : Optional[List[str]], default None
            List of command-line arguments to pass to the command. If None, no arguments are provided.

        Returns
        -------
        Optional[Any]
            The output produced by the command's `handle` method if execution is successful.
            Returns None if the command does not produce a result or if an error occurs.

        Raises
        ------
        CLIOrionisValueError
            If the command with the specified signature is not found in the registry.
        SystemExit
            If argument parsing fails due to invalid arguments provided (raised by argparse).
        Exception
            Propagates any exception raised during command execution after logging and error output.

        Notes
        -----
        - Logs execution start, completion, and errors with timestamps if enabled.
        - Handles argument parsing and injects parsed arguments into the command instance.
        - All exceptions are logged and displayed in the console.
        """

        # Scope Request instances to this command execution context
        with self.__app.createContext():

            # Ensure commands are loaded before attempting to execute
            self.__loadCommands()

            # Retrieve the command from the registry by its signature
            command: Command = self.__commands.get(signature)
            if command is None:
                raise CLIOrionisValueError(f"Command '{signature}' not found.")

            # Start execution timer for performance measurement
            self.__performance_counter.start()

            # Log the command execution start with RUNNING state if timestamps are enabled
            if command.timestamps:
                self.__executer.running(program=signature)

            try:
                # Instantiate the command class using the application container
                command_instance: IBaseCommand = self.__app.make(command.obj)

                # Inject parsed arguments into the command instance
                dict_args = self.__parseArgs(command, args)

                # Only set arguments if the command instance has a setArguments method
                if ReflectionInstance(command_instance).hasMethod('setArguments'):
                    command_instance.setArguments(dict_args.copy())

                # Inject a scoped CLIRequest instance into the application container for the command's context
                self.__app.scopedInstance(ICLIRequest, CLIRequest(
                    command=signature,
                    args=dict_args.copy()
                ))

                # Execute the command's handle method asynchronously and capture its output
                output = await self.__app.callAsync(command_instance, 'handle')

                # Calculate elapsed time and log completion with DONE state if command.timestamps are enabled
                self.__performance_counter.stop()
                elapsed_time = round(self.__performance_counter.getSeconds(), 2)
                if command.timestamps:
                    self.__executer.done(program=signature, time=f"{elapsed_time}s")

                # Log successful execution in the logger service
                self.__logger.info(f"Command '{signature}' executed successfully in ({elapsed_time}) seconds.")

                # Return the output produced by the command, if any
                return output

            except Exception as e:

                # Log the error in the logger service
                self.__logger.error(f"Command '{signature}' execution failed: {e}")

                # Calculate elapsed time and log failure with ERROR state if command.timestamps are enabled
                self.__performance_counter.stop()
                elapsed_time = round(self.__performance_counter.getSeconds(), 2)
                if command.timestamps:
                    self.__executer.fail(program=signature, time=f"{elapsed_time}s")

                # Propagate the exception after logging
                raise