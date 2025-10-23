from typing import Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from orionis.console.base.command import BaseCommand
from orionis.console.contracts.schedule import ISchedule
from orionis.console.exceptions import CLIOrionisRuntimeError
from orionis.foundation.contracts.application import IApplication

class ScheduleListCommand(BaseCommand):
    """
    Displays a list of all scheduled jobs registered in the Orionis application.

    This command retrieves scheduled tasks from the ISchedule service and presents them
    in a formatted table using the rich library. It provides details such as signature,
    arguments, purpose, random delay, start and end dates, and additional details for
    each scheduled job.

    Attributes
    ----------
    timestamps : bool
        Indicates whether timestamps will be shown in the command output.
    signature : str
        Command signature for invocation.
    description : str
        Description of the command.
    """

    # Indicates whether timestamps will be shown in the command output
    timestamps: bool = False

    # Command signature and description
    signature: str = "schedule:list"

    # Command description
    description: str = "Lists all scheduled jobs defined in the application."

    async def handle(self, app: IApplication, console: Console) -> None:
        """
        Displays a table of scheduled jobs defined in the application.

        This method dynamically retrieves the scheduler instance and the ISchedule service
        from the application, registers scheduled tasks, and fetches the list of scheduled
        jobs. It then prints the jobs in a formatted table using the rich library. If no
        jobs are found, a message is displayed. Any errors encountered during the process
        are reported as CLIOrionisRuntimeError.

        Parameters
        ----------
        app : IApplication
            The application instance providing configuration and service resolution.
        console : Console
            The rich Console instance used for output.

        Returns
        -------
        None
        """
        try:

            # Retrieve the Scheduler instance from the application
            scheduler = app.getScheduler()

            # Create an instance of the ISchedule service
            schedule_service: ISchedule = app.make(ISchedule)

            # Register scheduled tasks using the Scheduler's tasks method
            await scheduler.tasks(schedule_service)

            # Retrieve the list of scheduled jobs/events
            list_tasks: List[Dict] = schedule_service.events()

            # Display a message if no scheduled jobs are found
            if not list_tasks:
                console.line()
                console.print(Panel("No scheduled jobs found.", border_style="green"))
                console.line()

            # Create and configure a table to display scheduled jobs
            table = Table(title="Scheduled Jobs", show_lines=True)
            table.add_column("Signature", style="cyan", no_wrap=True)
            table.add_column("Arguments", style="magenta")
            table.add_column("Purpose", style="green")
            table.add_column("Random Delay (Calculated Result)", style="yellow")
            table.add_column("Start Date", style="white")
            table.add_column("End Date", style="white")
            table.add_column("Details", style="dim")

            # Populate the table with job details
            for job in list_tasks:
                signature = str(job.get("signature"))
                args = str(job.get("args", []))
                purpose = str(job.get("purpose"))
                random_delay = str(job.get("random_delay"))
                start_date = str(job.get("start_date"))
                end_date = str(job.get("end_date"))
                details = str(job.get("details"))

                table.add_row(signature, args, purpose, random_delay, start_date, end_date, details)

            # Print the table to the console
            console.line()
            console.print(table)
            console.line()

        except Exception as e:

            # Catch any unexpected exceptions and raise as a CLIOrionisRuntimeError
            raise CLIOrionisRuntimeError(
                f"An unexpected error occurred while listing the scheduled jobs: {e}"
            ) from e