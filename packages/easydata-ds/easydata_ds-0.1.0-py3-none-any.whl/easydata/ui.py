"""
Terminal UI for EasyData library using Rich for beautiful interfaces.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.text import Text
from rich import print as rprint

from .dataio import read_data, write_data, list_files, get_file_info, detect_file_type
from .decorator import DataFunction


class DataFunctionRunner:
    """
    Terminal UI runner for decorated data science functions.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """
        Initialize the runner.
        
        Args:
            console: Rich console instance (optional)
        """
        self.console = console or Console()
        self.functions: Dict[str, DataFunction] = {}
        self.current_directory = Path.cwd()
        
    def register_function(self, func: DataFunction) -> None:
        """
        Register a decorated function.
        
        Args:
            func: Decorated DataFunction instance
        """
        metadata = func.get_metadata()
        self.functions[metadata['name']] = func
        
    def discover_functions(self) -> None:
        """
        Discover decorated functions in the current module.
        """
        # Get the calling module
        frame = sys._getframe(2)
        module = frame.f_locals
        
        for name, obj in module.items():
            if isinstance(obj, DataFunction):
                self.register_function(obj)
        
        # Also check globals if we didn't find any functions
        if not self.functions:
            frame = sys._getframe(1)
            module = frame.f_globals
            
            for name, obj in module.items():
                if isinstance(obj, DataFunction):
                    self.register_function(obj)
    
    def show_welcome(self) -> None:
        """Display welcome message and available functions."""
        self.console.clear()
        
        welcome_text = Text("EasyData Function Runner", style="bold blue")
        self.console.print(Panel(welcome_text, title="Welcome"))
        
        if not self.functions:
            self.console.print("[red]No decorated functions found![/red]")
            self.console.print("Make sure to use @data_function decorator on your functions.")
            return
            
        # Show available functions
        table = Table(title="Available Functions")
        table.add_column("Function", style="cyan")
        table.add_column("Description", style="green")
        table.add_column("Input Types", style="yellow")
        table.add_column("Progress Bar?", style="magenta")
        
        for name, func in self.functions.items():
            metadata = func.get_metadata()
            table.add_row(
                name,
                metadata['description'] or "No description",
                ", ".join(metadata['input_types']),
                "Yes" if metadata['progress_enabled'] else "No"
            )
        
        self.console.print(table)
        self.console.print()
    
    def select_function(self) -> Optional[DataFunction]:
        """Let user select a function to run."""
        if not self.functions:
            return None
            
        function_names = list(self.functions.keys())
        
        if len(function_names) == 1:
            return self.functions[function_names[0]]
        
        self.console.print("[bold]Select a function to run:[/bold]")
        for i, name in enumerate(function_names, 1):
            metadata = self.functions[name].get_metadata()
            desc = metadata['description'] or "No description"
            self.console.print(f"{i}. {name} - {desc}")
        
        while True:
            try:
                choice = Prompt.ask("Enter function number", default="1")
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(function_names):
                    return self.functions[function_names[choice_idx]]
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")
    
    def browse_directory(self, start_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Browse directory and let user select a file.
        
        Args:
            start_dir: Starting directory (defaults to current directory)
            
        Returns:
            Selected file path or None if cancelled
        """
        current_dir = start_dir or self.current_directory
        
        while True:
            self.console.print(f"\n[bold]Current Directory:[/bold] {current_dir}")
            
            # List files in current directory
            files = list_files(current_dir)
            data_files = [f for f in files if detect_file_type(f) in ['csv', 'xlsx', 'json', 'parquet', 'tsv']]
            
            if not data_files:
                self.console.print("[yellow]No data files found in this directory.[/yellow]")
                if not Confirm.ask("Browse parent directory?"):
                    return None
                current_dir = current_dir.parent
                continue
            
            # Show files
            table = Table(title=f"Data Files in {current_dir.name}")
            table.add_column("#", style="cyan", width=3)
            table.add_column("File", style="green")
            table.add_column("Size", style="yellow")
            table.add_column("Type", style="magenta")
            
            for i, file_path in enumerate(data_files, 1):
                file_info = get_file_info(file_path)
                size = f"{file_info['size'] / 1024:.1f} KB" if file_info['size'] < 1024*1024 else f"{file_info['size'] / (1024*1024):.1f} MB"
                table.add_row(str(i), Path(file_path).name, size, file_info['extension'])
            
            self.console.print(table)
            
            # Show options
            self.console.print("\n[bold]Options:[/bold]")
            self.console.print("• Enter file number to select")
            self.console.print("• Enter '..' to go to parent directory")
            self.console.print("• Enter 'q' to quit")
            
            choice = Prompt.ask("Your choice")
            
            if choice.lower() == 'q':
                return None
            elif choice == '..':
                current_dir = current_dir.parent
                continue
            else:
                try:
                    file_idx = int(choice) - 1
                    if 0 <= file_idx < len(data_files):
                        return Path(data_files[file_idx])
                    else:
                        self.console.print("[red]Invalid file number.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a valid number or command.[/red]")
    
    def run_function_with_progress(self, func: DataFunction, data: pd.DataFrame, **kwargs) -> Any:
        """
        Run a function with progress tracking.
        
        Args:
            func: The DataFunction to execute
            data: Input DataFrame
            **kwargs: Additional arguments
            
        Returns:
            Function result
        """
        metadata = func.get_metadata()
        
        if not metadata['progress_enabled']:
            return func.execute(data, **kwargs)
        
        # Create progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task(f"Running {metadata['name']}...", total=len(data))
            
            # For now, we'll simulate progress by updating in batches
            # In a real implementation, you'd modify the function to accept a progress callback
            batch_size = metadata['batch_size']
            result = None
            
            for i in range(0, len(data), batch_size):
                batch = data.iloc[i:i+batch_size]
                result = func.execute(batch, **kwargs)
                progress.update(task, advance=len(batch))
            
            # If the function processes the whole dataset at once, update to 100%
            if len(data) <= batch_size:
                progress.update(task, completed=len(data))
            
            return result
    
    def run(self) -> None:
        """Main run loop for the terminal UI."""
        self.discover_functions()
        self.show_welcome()
        
        if not self.functions:
            return
        
        while True:
            # Select function
            func = self.select_function()
            if func is None:
                break
            
            # Browse for input file
            input_file = self.browse_directory()
            if input_file is None:
                break
            
            # Show file preview
            self.console.print(f"\n[bold]Selected file:[/bold] {input_file}")
            file_info = get_file_info(input_file)
            
            if 'error' in file_info:
                self.console.print(f"[red]Error reading file: {file_info['error']}[/red]")
                continue
            
            # Show file info
            info_table = Table(title="File Information")
            info_table.add_column("Property", style="cyan")
            info_table.add_column("Value", style="green")
            
            info_table.add_row("Size", f"{file_info['size'] / 1024:.1f} KB")
            info_table.add_row("Type", file_info['extension'])
            info_table.add_row("Columns", str(len(file_info['columns'])))
            info_table.add_row("Sample Rows", str(len(file_info['sample_rows'])))
            
            self.console.print(info_table)
            
            # Show sample data
            if file_info['sample_rows']:
                self.console.print("\n[bold]Sample Data:[/bold]")
                sample_df = pd.DataFrame(file_info['sample_rows'])
                self.console.print(sample_df.to_string())
            
            if not Confirm.ask("\nProceed with this file?"):
                continue
            
            try:
                # Read the data
                self.console.print(f"\n[bold]Reading data from {input_file}...[/bold]")
                data = read_data(input_file)
                self.console.print(f"[green]Loaded {len(data)} rows and {len(data.columns)} columns[/green]")
                
                # Run the function
                self.console.print(f"\n[bold]Running function: {func.get_metadata()['name']}[/bold]")
                result = self.run_function_with_progress(func, data)
                
                if result is not None:
                    self.console.print(f"[green]Function completed successfully![/green]")
                    
                    # Ask if user wants to save result
                    if isinstance(result, pd.DataFrame):
                        if Confirm.ask("Save result to file?"):
                            output_file = Prompt.ask("Enter output filename", default=f"output_{func.get_metadata()['name']}.csv")
                            write_data(result, output_file)
                            self.console.print(f"[green]Result saved to {output_file}[/green]")
                    
                    # Show result preview
                    if isinstance(result, pd.DataFrame):
                        self.console.print("\n[bold]Result Preview:[/bold]")
                        self.console.print(result.head().to_string())
                
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")
            
            # Ask if user wants to continue
            if not Confirm.ask("\nRun another function?"):
                break
        
        self.console.print("\n[bold green]Thank you for using EasyData![/bold green]")


def run_data_functions():
    """
    Convenience function to start the data function runner.
    Call this at the end of your script to start the UI.
    """
    runner = DataFunctionRunner()
    runner.run()
