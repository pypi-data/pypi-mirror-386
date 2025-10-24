"""
Core decorator functionality for EasyData library.
"""

import functools
import inspect
from typing import Callable, Any, Dict, List, Optional
from pathlib import Path
import pandas as pd


class DataFunction:
    """
    A decorator class that wraps data science functions and provides metadata
    about their expected inputs and outputs.
    """
    
    def __init__(self, 
                 description: str = "",
                 input_types: List[str] = None,
                 output_types: List[str] = None,
                 progress_enabled: bool = True,
                 batch_size: int = 1000):
        """
        Initialize the decorator with function metadata.
        
        Args:
            description: Human-readable description of what the function does
            input_types: List of supported input file types (e.g., ['csv', 'xlsx', 'json'])
            output_types: List of supported output file types (e.g., ['csv', 'xlsx'])
            progress_enabled: Whether to show progress bars for this function
            batch_size: Number of rows to process at once for progress tracking
        """
        self.description = description
        self.input_types = input_types or ['csv', 'xlsx', 'json', 'parquet']
        self.output_types = output_types or ['csv', 'xlsx']
        self.progress_enabled = progress_enabled
        self.batch_size = batch_size
        self.function = None
        self.function_name = None
        
    def __call__(self, func: Callable) -> 'DataFunction':
        """
        Apply the decorator to a function.
        
        Args:
            func: The function to decorate
            
        Returns:
            Self for chaining
        """
        self.function = func
        self.function_name = func.__name__
        
        # Preserve function metadata
        functools.wraps(func)(self)
        
        # Store the decorated function
        self._decorated_func = func
        
        return self
    
    def __getattr__(self, name):
        """Delegate attribute access to the wrapped function."""
        return getattr(self._decorated_func, name)
    
    def execute(self, data: pd.DataFrame, **kwargs) -> Any:
        """
        Execute the decorated function on the provided data.
        
        Args:
            data: The DataFrame to process
            **kwargs: Additional arguments to pass to the function
            
        Returns:
            The result of the function execution
        """
        if self.function is None:
            raise ValueError("No function has been decorated yet")
        
        # Get function signature to determine how to call it
        sig = inspect.signature(self.function)
        params = list(sig.parameters.keys())
        
        # If function takes 'data' as first parameter, pass it
        if params and params[0] == 'data':
            return self.function(data, **kwargs)
        # If function takes DataFrame as first parameter (by type annotation)
        elif params and sig.parameters[params[0]].annotation == pd.DataFrame:
            return self.function(data, **kwargs)
        # Otherwise, pass data as keyword argument
        else:
            return self.function(data=data, **kwargs)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this decorated function.
        
        Returns:
            Dictionary containing function metadata
        """
        return {
            'name': self.function_name,
            'description': self.description,
            'input_types': self.input_types,
            'output_types': self.output_types,
            'progress_enabled': self.progress_enabled,
            'batch_size': self.batch_size,
            'function': self.function
        }


def data_function(description: str = "",
                  input_types: List[str] = None,
                  output_types: List[str] = None,
                  progress_enabled: bool = True,
                  batch_size: int = 1000):
    """
    Decorator for data science functions that provides metadata and execution capabilities.
    
    Args:
        description: Human-readable description of what the function does
        input_types: List of supported input file types (e.g., ['csv', 'xlsx', 'json'])
        output_types: List of supported output file types (e.g., ['csv', 'xlsx'])
        progress_enabled: Whether to show progress bars for this function
        batch_size: Number of rows to process at once for progress tracking
        
    Example:
        @data_function(
            description="Add a new column with True/False based on condition",
            input_types=['csv', 'xlsx'],
            output_types=['csv']
        )
        def tag_condition(data):
            data['is_high_value'] = data['value'] > 100
            return data
    """
    def decorator(func):
        df = DataFunction(
            description=description,
            input_types=input_types,
            output_types=output_types,
            progress_enabled=progress_enabled,
            batch_size=batch_size
        )
        return df(func)
    
    return decorator
