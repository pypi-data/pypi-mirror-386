import datetime
import getpass
import inspect
import os
import sys
from typing import Optional
from rich.console import Console as RichConsole
from rich.panel import Panel
from rich.pretty import Pretty
from rich.theme import Theme
from rich.traceback import Traceback
from orionis.console.contracts.console import IConsole
from orionis.console.enums.styles import ANSIColors

class Console(IConsole):
    """
    Utility class for printing formatted messages to the console with ANSI colors.

    Provides methods to print success, info, warning, and error messages with
    optional timestamps, as well as general text formatting methods.
    """

    def __getTimestamp(self) -> str:
        """
        Returns the current date and time formatted in a muted color.

        Returns
        -------
        str
            The formatted timestamp with muted color.
        """
        return f"{ANSIColors.TEXT_MUTED.value}{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{ANSIColors.DEFAULT.value}"

    def __printWithBackground(self, label: str, bg_color: ANSIColors, message: str, timestamp: bool) -> None:
        """
        Prints a formatted message with a background color.

        Parameters
        ----------
        label : str
            The label to display (e.g., 'SUCCESS', 'INFO').
        bg_color : ANSIColors
            The background color to use.
        message : str
            The message to print.
        timestamp : bool
            Whether to include a timestamp.
        """
        str_time = self.__getTimestamp() if timestamp else ''
        print(f"{bg_color.value}{ANSIColors.TEXT_WHITE.value} {label} {ANSIColors.DEFAULT.value} {str_time} {message}{ANSIColors.DEFAULT.value}")

    def __printColored(self, message: str, text_color: ANSIColors) -> None:
        """
        Prints a message with a specified text color.

        Parameters
        ----------
        message : str
            The message to print.
        text_color : ANSIColors
            The text color to use.
        """
        print(f"{text_color.value}{message}{ANSIColors.DEFAULT.value}")

    def success(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a success message with a green background.

        Parameters
        ----------
        message : str, optional
            The success message to print.
        timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        self.__printWithBackground("SUCCESS", ANSIColors.BG_SUCCESS, message, timestamp)

    def textSuccess(self, message: str) -> None:
        """
        Prints a success message in green.

        Parameters
        ----------
        message : str
            The success message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_SUCCESS)

    def textSuccessBold(self, message: str) -> None:
        """
        Prints a bold success message in green.

        Parameters
        ----------
        message : str
            The success message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_BOLD_SUCCESS)

    def info(self, message: str, timestamp: bool = True) -> None:
        """
        Prints an informational message with a blue background.

        Parameters
        ----------
        message : str
            The informational message to print.
            timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        self.__printWithBackground("INFO", ANSIColors.BG_INFO, message, timestamp)

    def textInfo(self, message: str) -> None:
        """
        Prints an informational message in blue.

        Parameters
        ----------
        message : str
            The informational message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_INFO)

    def textInfoBold(self, message: str) -> None:
        """
        Prints a bold informational message in blue.

        Parameters
        ----------
        message : str
            The informational message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_BOLD_INFO)

    def warning(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a warning message with a yellow background.

        Parameters
        ----------
        message : str
            The warning message to print.
            timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        self.__printWithBackground("WARNING", ANSIColors.BG_WARNING, message, timestamp)

    def textWarning(self, message: str) -> None:
        """
        Prints a warning message in yellow.

        Parameters
        ----------
        message : str
            The warning message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_WARNING)

    def textWarningBold(self, message: str) -> None:
        """
        Prints a bold warning message in yellow.

        Parameters
        ----------
        message : str
            The warning message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_BOLD_WARNING)

    def fail(self, message: str, timestamp: bool = True) -> None:
        """
        Prints a failure message with a red background.

        Parameters
        ----------
        message : str
            The failure message to print.
            timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        self.__printWithBackground("FAIL", ANSIColors.BG_FAIL, message, timestamp)

    def error(self, message: str, timestamp: bool = True) -> None:
        """
        Prints an error message with a red background.

        Parameters
        ----------
        message : str
            The error message to print.
            timestamp : bool, optional
            Whether to include a timestamp (default is True).
        """
        self.__printWithBackground("ERROR", ANSIColors.BG_ERROR, message, timestamp)

    def textError(self, message: str) -> None:
        """
        Prints an error message in red.

        Parameters
        ----------
        message : str
            The error message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_ERROR)

    def textErrorBold(self, message: str) -> None:
        """
        Prints a bold error message in red.

        Parameters
        ----------
        message : str
            The error message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_BOLD_ERROR)

    def textMuted(self, message: str) -> None:
        """
        Prints a muted (gray) message.

        Parameters
        ----------
        message : str
            The message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_MUTED)

    def textMutedBold(self, message: str) -> None:
        """
        Prints a bold muted (gray) message.

        Parameters
        ----------
        message : str
            The message to print.
        """
        self.__printColored(message, ANSIColors.TEXT_BOLD_MUTED)

    def textUnderline(self, message: str) -> None:
        """
        Prints an underlined message.

        Parameters
        ----------
        message : str, optional
            The message to print.
        """
        print(f"{ANSIColors.TEXT_STYLE_UNDERLINE.value}{message}{ANSIColors.DEFAULT.value}")

    def clear(self) -> None:
        """
        Clears the console screen.

        Notes
        -----
        Uses the appropriate system command to clear the terminal screen based on the operating system.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

    def clearLine(self) -> None:
        """
        Clears the current line in the console.

        Notes
        -----
        Moves the cursor to the beginning of the line and overwrites it with a space, then returns the cursor to the start.
        """
        sys.stdout.write("\r \r")
        sys.stdout.flush()

    def line(self) -> None:
        """
        Prints a horizontal line in the console.

        Notes
        -----
        Outputs a newline character without advancing to a new line, effectively creating a visual separator.
        """
        print("\n", end="")

    def newLine(self, count: int = 1) -> None:
        """
        Prints multiple new lines.

        Parameters
        ----------
        count : int, optional
            The number of new lines to print (default is 1).

        Raises
        ------
        ValueError
            If count is less than or equal to 0.
        """
        if count <= 0:
            raise ValueError(f"Unsupported Value '{count}'")
        print("\n" * count, end="")

    def write(self, message: str) -> None:
        """
        Prints a message without moving to the next line.

        Parameters
        ----------
        message : str
            The message to print.
        """
        sys.stdout.write(f"{message}")
        sys.stdout.flush()

    def writeLine(self, message: str) -> None:
        """
        Prints a message and moves to the next line.

        Parameters
        ----------
        message : str, optional
            The message to print.
        """
        print(f"{message}")

    def ask(self, question: str) -> str:
        """
        Prompts the user for input with a message and returns the user's response.

        Parameters
        ----------
        question : str
            The question to ask the user.

        Returns
        -------
        str
            The user's input, as a string.
        """
        return input(f"{ANSIColors.TEXT_INFO.value}{str(question).strip()}{ANSIColors.DEFAULT.value} ")

    def confirm(self, question: str, default: bool = False) -> bool:
        """
        Asks a confirmation question and returns True or False based on the user's response.

        Parameters
        ----------
        question : str
            The confirmation question to ask.
        default : bool, optional
            The default response if the user presses Enter without typing a response.
            Default is False, which corresponds to a 'No' response.

        Returns
        -------
        bool
            The user's response, which will be True if 'Y' is entered,
            or False if 'N' is entered or the default is used.
        """
        response = input(f"{ANSIColors.TEXT_INFO.value}{str(question).strip()} (Y/n): {ANSIColors.DEFAULT.value} ").upper()
        return default if not response else str(response).upper in ["Y", "YES"]

    def secret(self, question: str) -> str:
        """
        Prompts the user for hidden input, typically used for password input.

        Parameters
        ----------
        question : str
            The prompt to ask the user.

        Returns
        -------
        str
            The user's hidden input, returned as a string.
        """
        return getpass.getpass(f"{ANSIColors.TEXT_INFO.value}{str(question).strip()}{ANSIColors.DEFAULT.value} ")

    def table(self, headers: list, rows: list) -> None:
        """
        Prints a table in the console with the given headers and rows, with bold headers.

        Parameters
        ----------
        headers : list of str
            The column headers for the table.
        rows : list of list of str
            The rows of the table, where each row is a list of strings representing the columns.

        Raises
        ------
        ValueError
            If headers or rows are empty.

        Notes
        -----
        The table adjusts column widths dynamically, includes bold headers, and uses box-drawing characters for formatting.
        """
        if not headers:
            raise ValueError("Headers cannot be empty.")
        if not rows:
            raise ValueError("Rows cannot be empty.")

        # Determine the maximum width of each column
        col_widths = [max(len(str(item)) for item in col) for col in zip(headers, *rows)]

        # Define border characters
        top_border = "┌" + "┬".join("─" * (col_width + 2) for col_width in col_widths) + "┐"
        separator = "├" + "┼".join("─" * (col_width + 2) for col_width in col_widths) + "┤"
        bottom_border = "└" + "┴".join("─" * (col_width + 2) for col_width in col_widths) + "┘"

        # Format the header row with bold text
        header_row = "│ " + " │ ".join(f"{ANSIColors.TEXT_BOLD.value}{header:<{col_width}}{ANSIColors.TEXT_RESET.value}" for header, col_width in zip(headers, col_widths)) + " │"

        # Print the table
        print(top_border)
        print(header_row)
        print(separator)

        for row in rows:
            row_text = "│ " + " │ ".join(f"{str(item):<{col_width}}" for item, col_width in zip(row, col_widths)) + " │"
            print(row_text)

        print(bottom_border)

    def anticipate(self, question: str, options: list, default=None) -> str:
        """
        Provides autocomplete suggestions based on user input.

        Parameters
        ----------
        question : str
            The prompt for the user.
        options : list of str
            The list of possible options for autocomplete.
        default : str, optional
            The default value if no matching option is found. Defaults to None.

        Returns
        -------
        str
            The chosen option or the default value.

        Notes
        -----
        This method allows the user to input a string, and then attempts to provide
        an autocomplete suggestion by matching the beginning of the input with the
        available options. If no match is found, the method returns the default value
        or the user input if no default is provided.
        """
        # Prompt the user for input
        input_value = input(f"{ANSIColors.TEXT_INFO.value}{str(question).strip()}{ANSIColors.DEFAULT.value} ")

        # Find the first option that starts with the input value, or use the default value
        return next((option for option in options if option.startswith(input_value)), default or input_value)

    def choice(self, question: str, choices: list, default_index: int = 0) -> str:
        """
        Allows the user to select an option from a list.

        Parameters
        ----------
        question : str
            The prompt for the user.
        choices : list of str
            The list of available choices.
        default_index : int, optional
            The index of the default choice (zero-based). Defaults to 0.

        Returns
        -------
        str
            The selected choice.

        Raises
        ------
        ValueError
            If `default_index` is out of the range of choices.

        Notes
        -----
        The user is presented with a numbered list of choices and prompted to select
        one by entering the corresponding number. If an invalid input is provided,
        the user will be repeatedly prompted until a valid choice is made.
        """
        if not choices:
            raise ValueError("The choices list cannot be empty.")

        if not (0 <= default_index < len(choices)):
            raise ValueError(f"Invalid default_index {default_index}. Must be between 0 and {len(choices) - 1}.")

        # Display the question and the choices
        print(f"{ANSIColors.TEXT_INFO.value}{question.strip()} (default: {choices[default_index]}):{ANSIColors.DEFAULT.value}")

        for idx, choice in enumerate(choices, 1):
            print(f"{ANSIColors.TEXT_MUTED.value}{idx}: {choice}{ANSIColors.DEFAULT.value}")

        # Prompt the user for input
        answer = input("Answer: ").strip()

        # If the user provides no input, select the default choice
        if not answer:
            return choices[default_index]

        # Validate input: ensure it's a number within range
        while not answer.isdigit() or not (1 <= int(answer) <= len(choices)):
            answer = input("Please select a valid number: ").strip()

        return choices[int(answer) - 1]

    def exception(self, e: Exception) -> None:
        """
        Prints an exception message with detailed information.

        Parameters
        ----------
        exception : Exception
            The exception to print.

        Notes
        -----
        This method prints the exception type, message, and a detailed stack trace.
        """
        rc = RichConsole()
        tb = Traceback.from_exception(
            type(e),
            e,
            e.__traceback__,
            max_frames=1,
            suppress=[],
            extra_lines=1,
            show_locals=False
        )
        rc.print(tb)

    def exitSuccess(self, message: str = None) -> None:
        """
        Exits the program with a success message.

        Parameters
        ----------
        message : str, optional
            The success message to print before exiting.
        """
        if message:
            self.success(message)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
            raise

    def exitError(self, message: str = None) -> None:
        """
        Exits the program with an error message.

        Parameters
        ----------
        message : str, optional
            The error message to print before exiting.
        """
        if message:
            self.error(message)
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
            raise

    def dump( # NOSONAR
        self,
        *args,
        show_types: bool = True,
        show_index: bool = False,
        expand_all: bool = True,
        max_depth: int | None = None,
        module_path: str | None = None,
        line_number: int | None = None,
        force_exit: bool = False,
        redirect_output: bool = False,
        insert_line: bool = False
    ) -> Optional[str]:
        """
        Displays formatted debug information for one or more variables using Rich, and optionally exports the output as HTML.

        Parameters
        ----------
        *args : Any
            One or more objects to be displayed for debugging.
        show_types : bool, optional
            If True, displays the type of each argument in the panel title. Default is True.
        show_index : bool, optional
            If True, shows an index number for each argument. Default is False.
        expand_all : bool, optional
            If True, expands all nested data structures. Default is True.
        max_depth : int or None, optional
            Maximum depth for nested structures. If None, no limit is applied. Default is None.
        module_path : str or None, optional
            Overrides the module path shown in the header. If None, uses the caller's module path.
        line_number : int or None, optional
            Overrides the line number shown in the header. If None, uses the caller's line number.
        force_exit : bool, optional
            If True, terminates the program after dumping. Default is False.
        redirect_output : bool, optional
            If True, temporarily restores stdout/stderr to their original streams during output. Default is False.
        insert_line : bool, optional
            If True, inserts a blank line before and after the dump output for better readability. Default

        Returns
        -------
        Optional[str]
            An HTML string containing the formatted output if successful, or None if caller information is unavailable.

        Notes
        -----
        This method uses the Rich library to display variables in a visually enhanced format, including type and index information if specified. It can also export the output as HTML for further use.
        """

        # Optionally redirect output to original stdout/stderr
        if redirect_output:
            original_stdout, original_stderr = sys.stdout, sys.stderr
            sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

        try:

            # Optionally insert a blank line before the dump output
            if insert_line:
                print()

            # Create a custom Rich theme for styling the dump output
            console = RichConsole(
                theme=Theme({
                    "dump.index": "bold bright_blue",
                    "dump.type": "bold green",
                    "dump.rule": "bright_black",
                }),
                record=True
            )
            width = console.size.width

            # If no module_path or line_number provided, get from caller
            if not module_path or not line_number:

                # Use inspect to get the caller's frame information
                caller_frame = inspect.currentframe()

                # If the frame is available, navigate back to the caller's frame
                if caller_frame is not None:

                    # Go back two frames to get the caller of the dump method
                    caller_frame = caller_frame.f_back.f_back

                    # If caller_frame is still valid, extract module and line number
                    if caller_frame is not None:

                        # If module_path or line_number not provided, get from caller
                        if not module_path:
                            module_path = caller_frame.f_globals.get("__name__", "unknown")
                        if not line_number:
                            line_number = caller_frame.f_lineno
                else:

                    #fallback if frame info is unavailable
                    module_path = "unknown"
                    line_number = '?'

            # Print header with module and line information
            header = f"🐞 [white]Module([/white][bold blue]{module_path}[/bold blue][white]) [/white][grey70]#{line_number}[/grey70]"
            console.print(header)

            # Iterate over each argument and display it in a styled panel
            for i, arg in enumerate(args):
                var_title = ""
                if show_index:
                    var_title += f"[dump.index]#{i+1}[/dump.index] "
                if show_types:
                    var_title += f"[dump.type]{type(arg).__name__}[/dump.type]"

                panel = Panel(
                    Pretty(
                        arg,
                        indent_size=2,
                        indent_guides=True,
                        expand_all=expand_all,
                        max_depth=max_depth,
                        margin=1,
                        insert_line=False,
                    ),
                    title=var_title if var_title else None,
                    title_align="left" if var_title else None,
                    border_style="dump.rule",
                    width=min(int(width * 0.85), 120),
                    padding=(0, 1),
                )
                console.print(panel)

            # Optionally insert a blank line before the dump output
            if insert_line:
                print()

            # Optionally terminate the program after dumping
            if force_exit:
                if redirect_output:
                    os._exit(1)
                else:
                    sys.exit(1)

            # Export the output as HTML and return it
            return console.export_html(inline_styles=True)

        finally:

            # Restore stdout/stderr if they were redirected
            if redirect_output:
                sys.stdout, sys.stderr = original_stdout, original_stderr
