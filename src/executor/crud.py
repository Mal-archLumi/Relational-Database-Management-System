"""
Simple CRUD operations executor
"""
from typing import List, Tuple, Any, Dict
from ..core.exceptions import ExecutionError
from ..storage.encryption import ColumnEncryptor

class CRUDExecutor:
    """Executes basic CRUD operations"""
    
    def __init__(self, file_manager, catalog):
        self.file_manager = file_manager
        self.catalog = catalog
        self.encryptor = ColumnEncryptor()
    
    def execute(self, parsed: Dict) -> List[Tuple]:
        """Execute a parsed SQL command"""
        command = parsed['command']
        
        if command == 'CREATE_TABLE':
            return self.create_table(parsed)
        elif command == 'INSERT':
            return self.insert(parsed)
        elif command == 'SELECT':
            return self.select(parsed)
        elif command == 'DROP_TABLE':
            return self.drop_table(parsed)
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
        
        # Encrypt values if needed
        encrypted_values = []
        for col_name, value in zip(table.get_column_names(), validated_values):
            col = table.columns[col_name]
            if col.encrypted and value is not None:
                column_id = f"{table_name}.{col_name}"
                encrypted_value = self.encryptor.encrypt_value(column_id, str(value))
                encrypted_values.append(encrypted_value)
            else:
                encrypted_values.append(value)
        
        # Save to disk
        self.file_manager.insert_row(table_name, encrypted_values)
        
        print(f"1 row inserted into '{table_name}'")
        return []
    
    def select(self, parsed: Dict) -> List[Tuple]:
        """Execute SELECT * FROM table"""
        table_name = parsed['table']
        columns = parsed['columns']
        
        # Get table schema
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # Get all rows from disk
        rows = self.file_manager.get_all_rows(table_name)
        
        # Decrypt encrypted values
        decrypted_rows = []
        for row in rows:
            decrypted_row = []
            for col_name, value in zip(table.get_column_names(), row):
                col = table.columns[col_name]
                if col.encrypted and value is not None:
                    column_id = f"{table_name}.{col_name}"
                    try:
                        decrypted_value = self.encryptor.decrypt_value(column_id, value)
                        decrypted_row.append(decrypted_value)
                    except:
                        decrypted_row.append("[ENCRYPTED]")
                else:
                    decrypted_row.append(value)
            decrypted_rows.append(tuple(decrypted_row))
        
        # Filter columns if needed
        if columns != ['*']:
            col_indices = []
            for col in columns:
                if col in table.columns:
                    col_indices.append(list(table.columns.keys()).index(col))
                else:
                    raise ExecutionError(f"Column '{col}' does not exist")
            
            result = []
            for row in decrypted_rows:
                result.append(tuple(row[i] for i in col_indices))
        else:
            result = decrypted_rows
        
        # Print result nicely
        if result:
            print(f"\n{len(result)} row(s) returned:")
            for row in result:
                print(f"  {row}")
        else:
            print("\nNo rows found")
        
        return result
    
    def drop_table(self, parsed: Dict) -> List[Tuple]:
        """Execute DROP TABLE"""
        table_name = parsed['table']
        
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        # Remove from catalog
        del self.catalog.tables[table_name]
        
        # Remove files
        import os
        csv_file = self.file_manager.table_file(table_name)
        schema_file = self.file_manager.schema_file(table_name)
        
        if os.path.exists(csv_file):
            os.remove(csv_file)
        if os.path.exists(schema_file):
            os.remove(schema_file)
        
        print(f"Table '{table_name}' dropped successfully")
        return []