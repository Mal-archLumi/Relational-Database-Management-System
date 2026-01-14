"""
Main database interface
"""

import os
import glob
from typing import List, Tuple, Any, Optional
from .exceptions import DatabaseError
from ..storage.file_manager import FileManager
from ..catalog.schema import Catalog, TableSchema
from ..parser.parser import SimpleParser
from ..executor.crud import CRUDExecutor

class Database:
    """Main database class"""
    
    def __init__(self, db_file: str = "default.maldb"):
        """
        Initialize or connect to a database
        
        Args:
            db_file: Path to database file (.maldb extension)
        """
        self.db_file = db_file
        self.file_manager = FileManager(db_file)
        self.catalog = Catalog()
        self.parser = SimpleParser()
        self.executor = CRUDExecutor(self.file_manager, self.catalog)
        
        # Load existing tables
        self._load_tables()
    
    def _load_tables(self):
        """Load all table schemas from disk"""
        # Get all schema files
        schema_files = glob.glob(os.path.join(self.file_manager.data_dir, "*_schema.json"))
        
        for schema_file in schema_files:
            table_name = os.path.basename(schema_file).replace("_schema.json", "")
            
            try:
                schema_dict = self.file_manager.load_schema(table_name)
                if schema_dict:
                    table = TableSchema.from_dict(schema_dict)
                    self.catalog.tables[table_name] = table
                    # print(f"Loaded table: {table_name}")
            except Exception as e:
                print(f"Warning: Could not load table {table_name}: {e}")
    
    def execute(self, sql: str) -> List[Tuple]:
        """
        Execute a SQL statement
        
        Args:
            sql: SQL statement string
            
        Returns:
            List of tuples representing rows
        """
        try:
            # Parse SQL
            parsed = self.parser.parse(sql)
            
            # Execute command
            result = self.executor.execute(parsed)
            
            return result
            
        except Exception as e:
            raise DatabaseError(f"Error: {e}")
    
    def close(self):
        """Close database connection"""
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()