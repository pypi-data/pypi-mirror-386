from orionis.console.base.command import BaseCommand
from orionis.console.contracts.reactor import IReactor
from orionis.console.exceptions import CLIOrionisRuntimeError
from rich.console import Console
from rich.panel import Panel

class HelpCommand(BaseCommand):
    """
    Provides usage instructions and lists all available commands for the Orionis CLI.

    This command displays a formatted help message including usage examples, a summary of all registered commands, and their descriptions. It is intended to guide users in understanding the available CLI functionality and command syntax.

    Attributes
    ----------
    timestamps : bool
        Indicates whether timestamps will be shown in the command output.
    signature : str
        Command signature.
    description : str
        Command description.

    Methods
    -------
    handle(reactor, console)
        Displays usage information and a list of available commands.
    """

    # Indicates whether timestamps will be shown in the command output
    timestamps: bool = False

    # Command signature and description
    signature: str = "help"

    # Command description
    description: str = "Displays usage information, examples, and a list of available commands in the Orionis CLI."

    def handle(self, reactor: IReactor, console: Console) -> dict:
        """
        Displays usage information and a list of available commands for the Orionis CLI.

        Parameters
        ----------
        reactor : IReactor
            The reactor instance providing command metadata via the `info()` method.

        Returns
        -------
        dict
            A dictionary containing the list of available commands, each with its signature and description.

        Raises
        ------
        CLIOrionisRuntimeError
            If an unexpected error occurs during help information generation or display.
        """
        try:

            # Retrieve the list of available commands from the reactor
            # List of dicts with 'signature' and 'description'
            commands = reactor.info()

            # Build the usage and commands help text
            usage = "[bold cyan]Usage:[/]\n  python -B <command> <params/flags>\n\n"
            usage += "[bold cyan]Example:[/]\n  python -B app:command --flag\n\n"
            usage += "[bold cyan]Available Commands:[/]\n"

            # Determine the maximum signature length for alignment
            max_sig_len = max((len(cmd['signature']) for cmd in commands), default=0)

            # Append each command's signature and description to the usage string
            for cmd in commands:
                usage += f"  [bold yellow]{cmd['signature']:<{max_sig_len}}[/]  {cmd['description']}\n"

            # Add options section
            usage += (
                "\n[bold cyan]Options:[/]\n"
                "  -h, --help    Show this help message and exit"
            )

            # Create a rich panel to display the help information
            panel = Panel(
                usage,
                title="[bold green]Orionis CLI Help[/]",
                expand=False,
                border_style="bright_blue",
                padding=(1, 2)
            )

            # Print the panel to the console
            console.print()
            console.print(panel)
            console.print()

            # Return the list of commands for potential further use
            return commands

        except Exception as e:

            # Raise a custom runtime error if any exception occurs
            raise CLIOrionisRuntimeError(f"An unexpected error occurred: {e}") from e
