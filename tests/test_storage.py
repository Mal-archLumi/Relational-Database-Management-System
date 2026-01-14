"""
Tests for storage layer
"""
import os
import tempfile
import pytest
from src.storage.file_manager import FileManager

def test_file_manager_creation():
    """Test FileManager initialization"""
    with tempfile.NamedTemporaryFile(suffix='.maldb') as tmp:
        fm = FileManager(tmp.name)
        
        # Test table file path
        table_file = fm.table_file('test_table')
        assert 'test_table.csv' in table_file
        
        # Test schema file path
        schema_file = fm.schema_file('test_table')
        assert 'test_table_schema.json' in schema_file

def test_schema_save_load():
    """Test saving and loading schema"""
    with tempfile.NamedTemporaryFile(suffix='.maldb') as tmp:
        fm = FileManager(tmp.name)
        
        # Save schema
        schema = {'name': 'test', 'columns': [{'name': 'id', 'type': 'INT'}]}
        fm.save_schema('test_table', schema)
        
        # Load schema
        loaded = fm.load_schema('test_table')
        assert loaded == schema

def test_insert_and_retrieve():
    """Test inserting and retrieving rows"""
    with tempfile.NamedTemporaryFile(suffix='.maldb') as tmp:
        fm = FileManager(tmp.name)
        
        # Insert rows
        fm.insert_row('test_table', [1, 'Alice', 25])
        fm.insert_row('test_table', [2, 'Bob', 30])
        
        # Retrieve rows
        rows = fm.get_all_rows('test_table')
        assert len(rows) == 2
        assert rows[0] == ['1', 'Alice', '25']
        assert rows[1] == ['2', 'Bob', '30']