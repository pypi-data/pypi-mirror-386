"""
Command-line interface for EasyData.
"""

import click
from rich.console import Console
from .ui import DataFunctionRunner
from .decorator import DataFunction

console = Console()


@click.command()
@click.option('--version', is_flag=True, help='Show version information')
@click.option('--help-functions', is_flag=True, help='Show available functions')
def main(version, help_functions):
    """
    EasyData - Data Science Function Runner
    
    A Python library for data scientists to easily apply functions to datasets
    with a terminal UI for browsing and selecting files.
    """
    if version:
        from . import __version__
        console.print(f"EasyData version {__version__}")
        return
    
    if help_functions:
        console.print("[bold]EasyData Functions[/bold]")
        console.print("Use @data_function decorator to create interactive data processing functions.")
        console.print("\nExample:")
        console.print("""
from easydata import data_function, run_data_functions

@data_function(description="My data function")
def my_function(data):
    return data

if __name__ == "__main__":
    run_data_functions()
""")
        return
    
    # Start the interactive UI
    runner = DataFunctionRunner()
    runner.run()


if __name__ == '__main__':
    main()
