"""
Enhanced CRUD executor with WHERE clause support
"""
from typing import List, Tuple, Any, Dict
from ..core.exceptions import ExecutionError
from ..storage.encryption import ColumnEncryptor
from .join import JoinExecutor

class CRUDExecutor:
    """Executes basic CRUD operations with WHERE clause support"""
    
    def __init__(self, file_manager, catalog, encryptor=None):  # Add encryptor parameter
        self.file_manager = file_manager
        self.catalog = catalog
        self.encryptor = encryptor or ColumnEncryptor()  # Use provided encryptor or create new
        self.join_executor = JoinExecutor(file_manager, catalog, self.encryptor)
    
    def execute(self, parsed: Dict) -> List[Tuple]:
        """Execute a parsed SQL command"""
        command = parsed['command']
        
        if command == 'CREATE_TABLE':
            return self.create_table(parsed)
        elif command == 'INSERT':
            return self.insert(parsed)
        elif command == 'SELECT':
            return self.select(parsed)
        elif command == 'UPDATE':
            return self.update(parsed)
        elif command == 'DELETE':
            return self.delete(parsed)
        elif command == 'DROP_TABLE':
            return self.drop_table(parsed)
        elif command == 'EXPLAIN':
            return self.explain(parsed)
        elif command == 'HELP':
            return self.help()
        elif command == 'JOIN':
            return self.join(parsed)
        else:
            raise ExecutionError(f"Unsupported command: {command}")
    
    def create_table(self, parsed: Dict) -> List[Tuple]:
        """Execute CREATE TABLE"""
        table_name = parsed['table']
        columns = parsed['columns']
        
        # Validate table name
        if not table_name or not table_name.isidentifier():
            raise ExecutionError(f"Invalid table name: {table_name}")
        
        # Check for duplicate column names
        col_names = [col.name for col in columns]
        if len(col_names) != len(set(col_names)):
            raise ExecutionError("Duplicate column names are not allowed")
        
        # Check for multiple primary keys
        primary_keys = [col.name for col in columns if col.primary_key]
        if len(primary_keys) > 1:
            raise ExecutionError("Only one PRIMARY KEY allowed per table")
        
        # Create table in catalog
        table = self.catalog.create_table(table_name, columns)
        
        # Save schema to disk
        self.file_manager.save_schema(table_name, table.to_dict())
        
        # Create empty CSV file
        with open(self.file_manager.table_file(table_name), 'w', newline='') as f:
            pass
        
        print(f"✅ Table '{table_name}' created successfully with {len(columns)} columns")
        return []
    
    def insert(self, parsed: Dict) -> List[Tuple]:
        """Execute INSERT with constraint enforcement"""
        table_name = parsed['table']
        values = parsed.get('values', [])
        columns = parsed.get('columns', None)
        
        # Get table schema
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # If columns specified, use them; otherwise use all columns in order
        if columns:
            col_names = columns
        else:
            col_names = table.get_column_names()
        
        # Validate values against schema
        try:
            validated_values = table.validate_row(values, col_names)
        except Exception as e:
            raise ExecutionError(f"Validation error: {e}")
        
        # Check constraints BEFORE inserting
        self._check_constraints_before_insert(table_name, table, col_names, validated_values)
        
        # Encrypt values if needed
        encrypted_values = []
        for col_name, value in zip(col_names, validated_values):
            col = table.columns[col_name]
            if col.encrypted and value is not None:
                column_id = f"{table_name}.{col_name}"
                encrypted_value = self.encryptor.encrypt_value(column_id, str(value))
                encrypted_values.append(encrypted_value)
            else:
                encrypted_values.append(value)
        
        # Save to disk
        self.file_manager.insert_row(table_name, encrypted_values)
        
        print(f"✅ 1 row inserted into '{table_name}'")
        return []
    
    def _check_constraints_before_insert(self, table_name: str, table, col_names: List[str], values: List):
        """Check constraints before inserting a row"""
        # Get all existing rows
        rows = self.file_manager.get_all_rows(table_name)
        
        # Convert values to string for comparison (but handle encryption)
        values_to_check = []
        for col_name, value in zip(col_names, values):
            col = table.columns[col_name]
            if col.encrypted and value is not None:
                column_id = f"{table_name}.{col_name}"
                encrypted_value = self.encryptor.encrypt_value(column_id, str(value))
                values_to_check.append(encrypted_value)
            else:
                values_to_check.append(str(value) if value is not None else None)
        
        # Check PRIMARY KEY constraint
        for col_name, value_to_check in zip(col_names, values_to_check):
            col = table.columns[col_name]
            if col.primary_key:
                # Check if value already exists
                col_index = list(table.columns.keys()).index(col_name)
                for row in rows:
                    if len(row) > col_index and row[col_index] == value_to_check:
                        # Get the actual value for error message
                        actual_value = values[col_names.index(col_name)]
                        raise ExecutionError(f"PRIMARY KEY constraint violation: value '{actual_value}' already exists in column '{col_name}'")
        
        # Check UNIQUE constraint
        for col_name, value_to_check in zip(col_names, values_to_check):
            col = table.columns[col_name]
            if col.unique:
                # Check if value already exists
                col_index = list(table.columns.keys()).index(col_name)
                for row in rows:
                    if len(row) > col_index and row[col_index] == value_to_check:
                        # Get the actual value for error message
                        actual_value = values[col_names.index(col_name)]
                        raise ExecutionError(f"UNIQUE constraint violation: value '{actual_value}' already exists in column '{col_name}'")
    
    def select(self, parsed: Dict) -> List[Tuple]:
        """Execute SELECT with WHERE clause support"""
        table_name = parsed['table']
        columns = parsed['columns']
        where_clause = parsed.get('where')
        
        # Get table schema
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # Get all rows from disk
        rows = self.file_manager.get_all_rows(table_name)
        
        # Process rows (decrypt, type conversion, filtering)
        processed_rows = []
        for row_idx, row in enumerate(rows):
            processed_row = []
            row_data = {}  # For WHERE clause evaluation
            
            for col_name, value in zip(table.get_column_names(), row):
                col = table.columns[col_name]
                
                # Handle NULL
                if value == '' or value is None:
                    processed_value = None
                else:
                    # Convert based on column type
                    if col.encrypted and value is not None:
                        column_id = f"{table_name}.{col_name}"
                        try:
                            processed_value = self.encryptor.decrypt_value(column_id, value)
                        except:
                            processed_value = "[ENCRYPTED]"
                    else:
                        try:
                            processed_value = col.validate(value)
                        except:
                            processed_value = value
                
                processed_row.append(processed_value)
                row_data[col_name] = processed_value
            
            # Apply WHERE clause if present
            if where_clause:
                try:
                    if self._evaluate_where(row_data, where_clause):
                        processed_rows.append(tuple(processed_row))
                except:
                    # If WHERE evaluation fails, include the row (simple approach)
                    processed_rows.append(tuple(processed_row))
            else:
                processed_rows.append(tuple(processed_row))
        
        # Filter columns if needed
        if columns != ['*']:
            col_indices = []
            for col in columns:
                if col in table.columns:
                    col_indices.append(list(table.columns.keys()).index(col))
                else:
                    raise ExecutionError(f"Column '{col}' does not exist in table '{table_name}'")
            
            result = []
            for row in processed_rows:
                result.append(tuple(row[i] for i in col_indices))
        else:
            result = processed_rows
        
        # Print result nicely
        if result:
            print(f"\n📊 {len(result)} row(s) returned:")
            for row in result:
                print(f"  {row}")
        else:
            print("\n📭 No rows found")
        
        return result
    
    def _evaluate_where(self, row_data: Dict, where_clause: str) -> bool:
        """Simple WHERE clause evaluation"""
        # Very simple evaluation for basic equality checks
        where_clause = where_clause.strip()
        
        # Check for simple equality: column = value
        if '=' in where_clause:
            parts = where_clause.split('=', 1)
            if len(parts) == 2:
                col_name = parts[0].strip()
                value_str = parts[1].strip().strip("'\"")
                
                if col_name in row_data:
                    # Simple string comparison for now
                    return str(row_data[col_name]) == value_str
        
        # Check for not equal: column != value
        elif '!=' in where_clause:
            parts = where_clause.split('!=', 1)
            if len(parts) == 2:
                col_name = parts[0].strip()
                value_str = parts[1].strip().strip("'\"")
                
                if col_name in row_data:
                    return str(row_data[col_name]) != value_str
        
        # Check for greater than: column > value
        elif '>' in where_clause and '>=' not in where_clause:
            parts = where_clause.split('>', 1)
            if len(parts) == 2:
                col_name = parts[0].strip()
                value_str = parts[1].strip().strip("'\"")
                
                if col_name in row_data:
                    try:
                        return float(row_data[col_name]) > float(value_str)
                    except:
                        return str(row_data[col_name]) > value_str
        
        # Default to True if we can't parse the WHERE clause
        return True
    
    def delete(self, parsed: Dict) -> List[Tuple]:
        """Execute DELETE statement"""
        table_name = parsed['table']
        where_clause = parsed.get('where')
        
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # Get all rows
        rows = self.file_manager.get_all_rows(table_name)
        
        # Find rows to delete (in reverse order to avoid index shifting)
        rows_to_delete = []
        for row_idx in range(len(rows) - 1, -1, -1):
            row = rows[row_idx]
            row_data = {}
            
            for col_name, value in zip(table.get_column_names(), row):
                col = table.columns[col_name]
                
                if value == '' or value is None:
                    row_data[col_name] = None
                else:
                    if col.encrypted and value is not None:
                        column_id = f"{table_name}.{col_name}"
                        try:
                            row_data[col_name] = self.encryptor.decrypt_value(column_id, value)
                        except:
                            row_data[col_name] = "[ENCRYPTED]"
                    else:
                        try:
                            row_data[col_name] = col.validate(value)
                        except:
                            row_data[col_name] = value
            
            # Check WHERE condition
            if where_clause:
                if not self._evaluate_where(row_data, where_clause):
                    continue
            
            rows_to_delete.append(row_idx)
        
        # Delete rows
        deleted_count = 0
        for row_idx in rows_to_delete:
            self._delete_row_by_index(table_name, row_idx)
            deleted_count += 1
        
        print(f"✅ {deleted_count} row(s) deleted from '{table_name}'")
        return []
    
    def _delete_row_by_index(self, table_name: str, row_index: int):
        """Delete a row by index"""
        import csv
        import os
        
        csv_file = self.file_manager.table_file(table_name)
        temp_file = csv_file + '.tmp'
        
        try:
            with open(csv_file, 'r', newline='') as infile, \
                 open(temp_file, 'w', newline='') as outfile:
                
                writer = csv.writer(outfile)
                reader = csv.reader(infile)
                
                for i, row in enumerate(reader):
                    if i != row_index:
                        writer.writerow(row)
            
            # Replace original file
            os.replace(temp_file, csv_file)
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
    
    def update(self, parsed: Dict) -> List[Tuple]:
        """Execute UPDATE statement"""
        table_name = parsed['table']
        set_values = parsed['set_values']
        where_clause = parsed.get('where')
        
        if not self.catalog.table_exists(table_name):
            raise ExecutionError(f"Table '{table_name}' does not exist")
        
        table = self.catalog.get_table(table_name)
        
        # Get all rows
        rows = self.file_manager.get_all_rows(table_name)
        updated_rows = 0
        
        # Process each row
        for row_idx, row in enumerate(rows):
            row_data = {}
            for col_name, value in zip(table.get_column_names(), row):
                col = table.columns[col_name]
                
                if value == '' or value is None:
                    row_data[col_name] = None
                else:
                    if col.encrypted and value is not None:
                        column_id = f"{table_name}.{col_name}"
                        try:
                            row_data[col_name] = self.encryptor.decrypt_value(column_id, value)
                        except:
                            row_data[col_name] = "[ENCRYPTED]"
                    else:
                        try:
                            row_data[col_name] = col.validate(value)
                        except:
                            row_data[col_name] = value
            
            # Check WHERE condition
            if where_clause:
                if not self._evaluate_where(row_data, where_clause):
                    continue
            
            # Update values
            for col_name, new_value in set_values.items():
                if col_name not in table.columns:
                    raise ExecutionError(f"Column '{col_name}' does not exist")
                
                col = table.columns[col_name]
                
                # Validate new value
                try:
                    validated_value = col.validate(new_value)
                except Exception as e:
                    raise ExecutionError(f"Invalid value for column '{col_name}': {e}")
                
                # Check constraints for updated value
                if col.primary_key or col.unique:
                    # Check if new value already exists in other rows
                    col_index = list(table.columns.keys()).index(col_name)
                    for other_row_idx, other_row in enumerate(rows):
                        if other_row_idx != row_idx and len(other_row) > col_index:
                            other_value = other_row[col_index]
                            # Decrypt if needed for comparison
                            if col.encrypted and other_value is not None:
                                column_id = f"{table_name}.{col_name}"
                                try:
                                    other_value = self.encryptor.decrypt_value(column_id, other_value)
                                except:
                                    other_value = "[ENCRYPTED]"
                            
                            if str(other_value) == str(validated_value):
                                raise ExecutionError(f"Constraint violation: value '{validated_value}' already exists in column '{col_name}'")
                
                # Encrypt if needed
                if col.encrypted and validated_value is not None:
                    column_id = f"{table_name}.{col_name}"
                    encrypted_value = self.encryptor.encrypt_value(column_id, str(validated_value))
                    row[list(table.columns.keys()).index(col_name)] = encrypted_value
                else:
                    row[list(table.columns.keys()).index(col_name)] = validated_value
            
            # Save updated row
            self.file_manager.update_row(table_name, row_idx, row)
            updated_rows += 1
        
        print(f"✅ {updated_rows} row(s) updated in '{table_name}'")
        return []
    
    def join(self, parsed: Dict) -> List[Tuple]:
        """Execute JOIN query"""
        table1 = parsed['table1']
        table2 = parsed['table2']
        on_clause = parsed['on_clause']
        columns = parsed['columns']
        
        # Perform join
        joined_rows = self.join_executor.inner_join(table1, table2, on_clause)
        
        # Filter columns if needed
        if columns != ['*']:
            # Simplified column filtering for JOIN
            # In a real implementation, you'd need to handle table prefixes
            result = joined_rows  # Return all columns for now
        else:
            result = joined_rows
        
        # Print result
        if result:
            print(f"\n🔗 JOIN result: {len(result)} row(s)")
            for row in result[:10]:  # Show first 10 rows
                print(f"  {row}")
            if len(result) > 10:
                print(f"  ... and {len(result) - 10} more rows")
        else:
            print("\n🔗 No matching rows found in JOIN")
        
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
        
        print(f"✅ Table '{table_name}' dropped successfully")
        return []
    
    def explain(self, parsed: Dict) -> List[Tuple]:
        """Execute EXPLAIN"""
        inner_query = parsed['inner_query']
        
        print(f"\n🔍 EXPLAIN Query Plan:")
        print(f"   Command: {inner_query['command']}")
        print(f"   Table: {inner_query.get('table', 'N/A')}")
        
        if inner_query['command'] == 'CREATE_TABLE':
            print(f"   Columns: {len(inner_query['columns'])}")
            for col in inner_query['columns']:
                constraints = []
                if col.primary_key: constraints.append("PRIMARY KEY")
                if col.unique: constraints.append("UNIQUE")
                if col.not_null: constraints.append("NOT NULL")
                if col.encrypted: constraints.append("ENCRYPTED")
                
                constr_str = f" ({', '.join(constraints)})" if constraints else ""
                print(f"     - {col.name}: {col.dtype_str}{constr_str}")
        
        elif inner_query['command'] == 'SELECT':
            print(f"   Columns: {inner_query['columns']}")
            if inner_query.get('where'):
                print(f"   WHERE: {inner_query['where']}")
        
        return []
    
    def help(self) -> List[Tuple]:
        """Show help"""
        print("\n📖 MALDB SQL Commands:")
        print("   CREATE TABLE name (col1 TYPE [CONSTRAINTS], col2 TYPE, ...)")
        print("   INSERT INTO table VALUES (val1, val2, ...)")
        print("   INSERT INTO table (col1, col2) VALUES (val1, val2)")
        print("   SELECT * FROM table [WHERE condition]")
        print("   UPDATE table SET column = value [WHERE condition]")
        print("   DELETE FROM table [WHERE condition]")
        print("   DROP TABLE name")
        print("   EXPLAIN query")
        print("   help;")
        print("   exit;")
        print("\n📋 Constraints: PRIMARY KEY, UNIQUE, NOT NULL, ENCRYPTED")
        print("📋 Data Types: INT, VARCHAR(N), TEXT, DECIMAL, BOOLEAN")
        return []