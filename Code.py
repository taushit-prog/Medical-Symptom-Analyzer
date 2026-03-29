# main.py
# ─────────────────────────────────────────────────────────────────────────────
# This is the ENTRY POINT of VaidyaAI — the file you run from the terminal.
#
# It uses the "Click" library to handle CLI commands and flags, and ties
# together all the other modules: analyzer, display, and history.
#
# Run options:
#   python main.py                  → Analyse symptoms (interactive prompts)
#   python main.py --history        → View past sessions
#   python main.py --clear-history  → Delete all saved sessions
# ─────────────────────────────────────────────────────────────────────────────

import sys                     # Built-in: for sys.exit() to quit the program cleanly
import click                   # Third-party: turns Python functions into CLI commands
from rich.console import Console   # Rich console for styled terminal output
from rich.prompt import Prompt, Confirm  # Rich's styled input prompts
from rich.progress import Progress, SpinnerColumn, TextColumn  # Loading spinner

# Our own modules
from analyzer import analyse_symptoms
from display  import print_banner, print_analysis, print_error, print_history_table
from history  import save_session, get_recent_sessions, clear_history


# A single shared Console object for this file (same pattern as display.py)
console = Console()


# ─── Click decorators ─────────────────────────────────────────────────────────
# @click.command() tells Click: "the function below is a CLI command".
# @click.option() adds optional flags the user can pass on the command line.
#
# How Click works:
#   - The decorator reads the CLI flags when the script runs.
#   - It passes their values as arguments to the function automatically.
#   - "is_flag=True" means the option is a boolean switch (present = True).
#   - "help=" sets the description shown in "python main.py --help".

@click.command()
@click.option("--history",       is_flag=True, default=False, help="Show past analysis sessions.")
@click.option("--clear-history", is_flag=True, default=False, help="Delete all saved sessions.")
def vaidya(history: bool, clear_history_flag: bool):
    """
    VaidyaAI — AI-Powered Medical Symptom Analyser.

    This docstring appears in the --help output automatically (Click feature).
    """

    # Always show the banner first, regardless of which mode we're in.
    print_banner()

    # ── Mode 1: Clear history ──────────────────────────────────────────────
    if clear_history_flag:
        # Confirm() asks the user "Are you sure?" with a y/n prompt.
        # If they say no (False), we abort with a message.
        confirmed = Confirm.ask("[yellow]This will delete all saved sessions. Continue?[/yellow]")
        if confirmed:
            deleted = clear_history()  # Returns True if a file was deleted
            if deleted:
                console.print("[green]Session history cleared.[/green]")
            else:
                console.print("[dim]No history file found — nothing to delete.[/dim]")
        else:
            console.print("[dim]Cancelled.[/dim]")
        return  # Stop here — don't continue to the main flow

    # ── Mode 2: View history ───────────────────────────────────────────────
    if history:
        sessions = get_recent_sessions(n=10)  # Fetch up to 10 recent sessions
        print_history_table(sessions)         # Display them as a Rich table
        return  # Stop here

    # ── Mode 3: Main symptom analysis (default mode) ───────────────────────
    run_analysis()


def run_analysis():
    """
    run_analysis() is the main interactive flow of VaidyaAI.
    It collects user input, calls Claude, and displays the result.
    Separated into its own function to keep vaidya() clean and readable.
    """

    # Print a styled section header using Rich markup
    console.print("[bold cyan]Please answer a few questions so we can help you.[/bold cyan]")
    console.print("[dim]Your data stays on your device — nothing is stored remotely.[/dim]\n")

    # ── Step 1: Collect patient profile ───────────────────────────────────
    # Prompt.ask() shows a styled question and waits for keyboard input.
    # It returns whatever the user typed as a string.

    # Age — we loop until we get a valid integer
    while True:
        age_str = Prompt.ask("[cyan]Your age[/cyan]")
        try:
            # int() converts the string to an integer.
            # If the string isn't a number, ValueError is raised.
            age = int(age_str)
            if age < 0 or age > 130:  # Sanity check — ages outside this range are invalid
                raise ValueError("Age out of realistic range")
            break  # Break out of the loop — we have a valid age
        except ValueError:
            # Tell the user and loop again (they get another chance to type)
            console.print("[red]Please enter a valid age (e.g. 25).[/red]")

    # Sex — we use choices to restrict input to valid options
    sex = Prompt.ask(
        "[cyan]Biological sex[/cyan]",
        choices=["male", "female", "other"],  # Click validates against this list
        default="other",                       # Default if they just press Enter
    )

    # Pre-existing conditions — free text, optional
    conditions = Prompt.ask(
        "[cyan]Any known conditions[/cyan] [dim](e.g. diabetes, asthma — press Enter to skip)[/dim]",
        default="",  # Empty string = user pressed Enter without typing
    )

    console.print()  # Blank line before the symptoms prompt

    # Symptoms — the main input, also free text
    console.print("[bold cyan]Describe your symptoms:[/bold cyan]")
    console.print("[dim]Be as detailed as possible — include location, duration, severity.[/dim]")

    # Prompt.ask() with no choices accepts any text
    symptoms = Prompt.ask("[cyan]>[/cyan]")

    # Basic validation — refuse empty input
    if not symptoms.strip():
        print_error("No symptoms entered. Please describe what you are experiencing.")
        sys.exit(1)  # sys.exit(1) quits the program with a non-zero code (signals error)

    console.print()

    # ── Step 2: Run the analysis with a loading spinner ────────────────────
    # Progress() creates a context manager that shows a live status bar.
    # SpinnerColumn() adds an animated spinning indicator.
    # TextColumn() shows a text label next to the spinner.
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/bold cyan]"),
        transient=True,   # transient=True removes the spinner once it's done
        console=console,
    ) as progress:

        # progress.add_task() registers a task and starts the spinner.
        # total=None means we don't know how long it'll take (indeterminate).
        task = progress.add_task("Consulting VaidyaAI — analysing symptoms...", total=None)

        try:
            # Call the analyser (this is the blocking API call to Claude)
            result = analyse_symptoms(symptoms, age, sex, conditions)

        except RuntimeError as e:
            # RuntimeError is what analyzer.py raises on any problem.
            # We stop the spinner and display the error.
            progress.stop()
            print_error(str(e))
            sys.exit(1)

    # ── Step 3: Display the result ─────────────────────────────────────────
    print_analysis(result)

    # ── Step 4: Save the session to local history ──────────────────────────
    try:
        save_session(symptoms, age, sex, conditions, result)
        console.print("[dim]Session saved. Run with --history to review past sessions.[/dim]\n")
    except Exception as e:
        # If saving fails, warn the user but don't crash — the analysis was the important part.
        console.print(f"[dim yellow]Could not save session: {e}[/dim yellow]\n")

    # ── Step 5: Offer to run again ─────────────────────────────────────────
    again = Confirm.ask("[cyan]Analyse another set of symptoms?[/cyan]", default=False)
    if again:
        console.print()
        run_analysis()  # Recursive call — runs the whole flow again
    else:
        console.print("\n[bold cyan]Stay safe. VaidyaAI signing off.[/bold cyan]\n")


# ─── Entry point guard ─────────────────────────────────────────────────────────
# This block only runs when main.py is executed DIRECTLY (python main.py).
# It does NOT run if main.py is imported as a module by another file.
# This is a Python best practice — always wrap your entry code in this guard.
if __name__ == "__main__":
    # Click needs the function name to match the decorator, so we call vaidya().
    # Click reads sys.argv (command-line arguments) automatically.
    vaidya()
