"""
Simple CRUD operations executor
"""
from typing import List, Tuple, Any, Dict
from ..core.exceptions import ExecutionError

class CRUDExecutor:
    """Executes basic CRUD operations"""
    
    def __init__(self, file_manager, catalog):
        self.file_manager = file_manager
        self.catalog = catalog
    
    def execute(self, parsed: Dict) -> List[Tuple]:
        """Execute a parsed SQL command"""
        command = parsed['command']
        
        if command == 'CREATE_TABLE':
            return self.create_table(parsed)
        elif command == 'INSERT':
            return self.insert(parsed)
        elif command == 'SELECT':
            return self.select(parsed)
        else:
            raise ExecutionError(f"Unsupported command: {command}")
    
    def create_table(self, parsed: Dict) -> List[Tuple]:
        """Execute CREATE TABLE"""
        table_name = parsed['table']
        columns = parsed['columns']
        
        # Create table in catalog
        table = self.catalog.create_table(table_name, columns)
        
        # Save schema to disk
        self.file_manager.save_schema(table_name, table.to_dict())
        
        # Create empty CSV file
        with open(self.file_manager.table_file(table_name), 'w', newline='') as f:
            pass
        
        print(f"Table '{table_name}' created successfully")
        return []
    
    def insert(self, parsed: Dict) -> List[Tuple]:
        """Execute INSERT"""
        table_name = parsed['table']
        values = parsed['values']
        
        # Get table schema
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # Validate values against schema
        try:
            validated_values = table.validate_row(values)
        except Exception as e:
            raise ExecutionError(f"Validation error: {e}")
        
        # Save to disk
        self.file_manager.insert_row(table_name, validated_values)
        
        print(f"1 row inserted into '{table_name}'")
        return []
    
    def select(self, parsed: Dict) -> List[Tuple]:
        """Execute SELECT * FROM table"""
        table_name = parsed['table']
        
        # Get all rows from disk
        rows = self.file_manager.get_all_rows(table_name)
        
        # Convert to tuples
        result = [tuple(row) for row in rows]
        
        # Print result nicely
        if result:
            print(f"\n{len(result)} row(s) returned:")
            for row in result:
                print(f"  {row}")
        else:
            print("\nNo rows found")
        
        return result