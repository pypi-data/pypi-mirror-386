"""
Data input/output operations for EasyData library.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional
import os


def detect_file_type(file_path: Union[str, Path]) -> str:
    """
    Detect the file type based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension without the dot (e.g., 'csv', 'xlsx')
    """
    path = Path(file_path)
    return path.suffix.lower().lstrip('.')


def read_data(file_path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Read data from various file formats into a pandas DataFrame.
    
    Args:
        file_path: Path to the data file
        **kwargs: Additional arguments to pass to pandas read functions
        
    Returns:
        pandas DataFrame containing the data
        
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file doesn't exist
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_type = detect_file_type(file_path)
    
    if file_type == 'csv':
        return pd.read_csv(file_path, **kwargs)
    elif file_type in ['xlsx', 'xls']:
        return pd.read_excel(file_path, **kwargs)
    elif file_type == 'json':
        return pd.read_json(file_path, **kwargs)
    elif file_type == 'parquet':
        return pd.read_parquet(file_path, **kwargs)
    elif file_type == 'tsv':
        return pd.read_csv(file_path, sep='\t', **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_type}")


def write_data(data: pd.DataFrame, 
               file_path: Union[str, Path], 
               **kwargs) -> None:
    """
    Write a pandas DataFrame to various file formats.
    
    Args:
        data: DataFrame to write
        file_path: Output file path
        **kwargs: Additional arguments to pass to pandas write functions
        
    Raises:
        ValueError: If file format is not supported
    """
    file_path = Path(file_path)
    file_type = detect_file_type(file_path)
    
    # Create directory if it doesn't exist
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if file_type == 'csv':
        data.to_csv(file_path, index=False, **kwargs)
    elif file_type in ['xlsx', 'xls']:
        data.to_excel(file_path, index=False, **kwargs)
    elif file_type == 'json':
        data.to_json(file_path, orient='records', **kwargs)
    elif file_type == 'parquet':
        data.to_parquet(file_path, index=False, **kwargs)
    elif file_type == 'tsv':
        data.to_csv(file_path, sep='\t', index=False, **kwargs)
    else:
        raise ValueError(f"Unsupported file format: {file_type}")


def list_files(directory: Union[str, Path], 
               extensions: Optional[list] = None) -> list:
    """
    List files in a directory with optional extension filtering.
    
    Args:
        directory: Directory to search
        extensions: List of file extensions to include (e.g., ['csv', 'xlsx'])
        
    Returns:
        List of file paths
    """
    directory = Path(directory)
    
    if not directory.exists():
        return []
    
    files = []
    for file_path in directory.iterdir():
        if file_path.is_file():
            if extensions is None:
                files.append(str(file_path))
            else:
                file_ext = detect_file_type(file_path)
                if file_ext in extensions:
                    files.append(str(file_path))
    
    return sorted(files)


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get information about a data file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {'exists': False}
    
    try:
        # Read a small sample to get basic info
        sample_data = read_data(file_path, nrows=5)
        
        return {
            'exists': True,
            'size': file_path.stat().st_size,
            'extension': detect_file_type(file_path),
            'columns': list(sample_data.columns),
            'dtypes': sample_data.dtypes.to_dict(),
            'shape': sample_data.shape,
            'sample_rows': sample_data.to_dict('records')
        }
    except Exception as e:
        return {
            'exists': True,
            'size': file_path.stat().st_size,
            'extension': detect_file_type(file_path),
            'error': str(e)
        }
