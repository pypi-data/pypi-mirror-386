"""
EasyData - A Python library for data scientists to easily apply functions to datasets
with a terminal UI for browsing and selecting files.
"""

from .decorator import data_function
from .ui import DataFunctionRunner, run_data_functions
from .dataio import read_data, write_data, detect_file_type

__version__ = "0.1.0"
__author__ = "Cole Ragone"
__email__ = "coleragone@example.com"
__description__ = "A Python library for data scientists to easily apply functions to datasets with a terminal UI"

__all__ = [
    "data_function", 
    "DataFunctionRunner", 
    "run_data_functions", 
    "read_data", 
    "write_data", 
    "detect_file_type"
]
