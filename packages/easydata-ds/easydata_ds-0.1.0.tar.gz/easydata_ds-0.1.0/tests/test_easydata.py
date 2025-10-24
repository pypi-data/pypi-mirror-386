"""
Tests for EasyData package.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os

from easydata import data_function, DataFunctionRunner, read_data, write_data, detect_file_type


class TestDataFunction:
    """Test the data_function decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator functionality."""
        
        @data_function(description="Test function")
        def test_func(data):
            return data
        
        assert hasattr(test_func, 'get_metadata')
        assert hasattr(test_func, 'execute')
        
        metadata = test_func.get_metadata()
        assert metadata['name'] == 'test_func'
        assert metadata['description'] == 'Test function'
    
    def test_decorator_execution(self):
        """Test function execution."""
        
        @data_function(description="Add column")
        def add_column(data):
            data['new_col'] = 'test'
            return data
        
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = add_column.execute(df)
        
        assert 'new_col' in result.columns
        assert result['new_col'].iloc[0] == 'test'


class TestDataIO:
    """Test data I/O functionality."""
    
    def test_detect_file_type(self):
        """Test file type detection."""
        assert detect_file_type('test.csv') == 'csv'
        assert detect_file_type('test.xlsx') == 'xlsx'
        assert detect_file_type('test.json') == 'json'
    
    def test_read_write_csv(self):
        """Test CSV read/write functionality."""
        df = pd.DataFrame({'a': [1, 2, 3], 'b': ['x', 'y', 'z']})
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write data
            write_data(df, temp_path)
            
            # Read data back
            result = read_data(temp_path)
            
            pd.testing.assert_frame_equal(df, result)
        finally:
            os.unlink(temp_path)


class TestDataFunctionRunner:
    """Test the DataFunctionRunner."""
    
    def test_runner_initialization(self):
        """Test runner initialization."""
        runner = DataFunctionRunner()
        assert isinstance(runner.functions, dict)
        assert len(runner.functions) == 0
    
    def test_function_registration(self):
        """Test function registration."""
        
        @data_function(description="Test function")
        def test_func(data):
            return data
        
        runner = DataFunctionRunner()
        runner.register_function(test_func)
        
        assert len(runner.functions) == 1
        assert 'test_func' in runner.functions


if __name__ == '__main__':
    pytest.main([__file__])
