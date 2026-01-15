#!/usr/bin/env python3
"""
Quick fix script for MALDB issues
"""
import os
import sys

def fix_crud_py():
    """Fix the crud.py file"""
    crud_path = "src/executor/crud.py"
    
    with open(crud_path, 'r') as f:
        content = f.read()
    
    # Fix Self -> self
    content = content.replace("Self.file_manager", "self.file_manager")
    
    with open(crud_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {crud_path}")

def create_join_py():
    """Create the missing join.py file"""
    join_content = '''"""
Basic JOIN implementation
"""
from typing import List, Tuple
from ..core.exceptions import ExecutionError

class JoinExecutor:
    """Handles basic JOIN operations"""
    
    def __init__(self, file_manager, catalog, encryptor):
        self.file_manager = file_manager
        self.catalog = catalog
        self.encryptor = encryptor
    
    def inner_join(self, table1: str, table2: str, on_clause: str) -> List[Tuple]:
        """
        Perform INNER JOIN on two tables
        
        Args:
            table1, table2: Table names
            on_clause: String like "table1.col = table2.col"
        """
        # Parse ON clause
        if '=' not in on_clause:
            raise ExecutionError("Invalid ON clause. Use: table1.column = table2.column")
        
        left_side, right_side = on_clause.split('=', 1)
        left_side = left_side.strip()
        right_side = right_side.strip()
        
        # Parse column references
        left_table, left_col = self._parse_column_ref(left_side)
        right_table, right_col = self._parse_column_ref(right_side)
        
        # Validate tables exist
        if not self.catalog.table_exists(table1):
            raise ExecutionError(f"Table '{table1}' does not exist")
        if not self.catalog.table_exists(table2):
            raise ExecutionError(f"Table '{table2}' does not exist")
        
        # Get table schemas
        t1_schema = self.catalog.get_table(table1)
        t2_schema = self.catalog.get_table(table2)
        
        # Get all rows
        t1_rows = self._get_decrypted_rows(table1, t1_schema)
        t2_rows = self._get_decrypted_rows(table2, t2_schema)
        
        # Perform join
        result = []
        
        for row1 in t1_rows:
            row1_dict = dict(zip(t1_schema.get_column_names(), row1))
            
            for row2 in t2_rows:
                row2_dict = dict(zip(t2_schema.get_column_names(), row2))
                
                # Check join condition
                if str(row1_dict.get(left_col, '')) == str(row2_dict.get(right_col, '')):
                    # Combine rows
                    combined_row = list(row1) + list(row2)
                    result.append(tuple(combined_row))
        
        return result
    
    def _parse_column_ref(self, column_ref: str):
        """Parse table.column reference"""
        if '.' in column_ref:
            parts = column_ref.split('.')
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()
        
        raise ExecutionError(f"Invalid column reference: {column_ref}. Use: table.column")
    
    def _get_decrypted_rows(self, table_name: str, schema):
        """Get all rows with decrypted values"""
        rows = self.file_manager.get_all_rows(table_name)
        decrypted_rows = []
        
        for row in rows:
            decrypted_row = []
            for col_name, value in zip(schema.get_column_names(), row):
                col = schema.columns[col_name]
                
                if value == '' or value is None:
                    decrypted_row.append(None)
                else:
                    if col.encrypted and value is not None:
                        column_id = f"{table_name}.{col_name}"
                        try:
                            decrypted_row.append(self.encryptor.decrypt_value(column_id, value))
                        except:
                            decrypted_row.append("[ENCRYPTED]")
                    else:
                        try:
                            decrypted_row.append(col.validate(value))
                        except:
                            decrypted_row.append(value)
            
            decrypted_rows.append(tuple(decrypted_row))
        
        return decrypted_rows
'''
    
    join_path = "src/executor/join.py"
    with open(join_path, 'w') as f:
        f.write(join_content)
    
    print(f"✅ Created {join_path}")

def add_update_to_file_manager():
    """Add update_row method to file_manager.py"""
    file_manager_path = "src/storage/file_manager.py"
    
    with open(file_manager_path, 'r') as f:
        content = f.read()
    
    # Check if update_row already exists
    if 'def update_row' in content:
        print(f"✅ update_row method already exists in {file_manager_path}")
        return
    
    # Add the method before the last line (usually a closing brace or empty)
    lines = content.split('\n')
    
    # Find a good place to insert - usually before the last line
    insert_index = len(lines) - 1
    for i, line in enumerate(lines):
        if line.strip() == '}' or line.strip() == ')' or line.strip() == '':
            insert_index = i
            break
    
    update_method = '''    def update_row(self, table_name: str, row_index: int, new_row: List):
        """Update a specific row in a table"""
        import csv
        import os
        
        csv_file = self.table_file(table_name)
        temp_file = csv_file + '.tmp'
        
        try:
            with open(csv_file, 'r', newline='') as infile, \\
                 open(temp_file, 'w', newline='') as outfile:
                
                writer = csv.writer(outfile)
                reader = csv.reader(infile)
                
                for i, row in enumerate(reader):
                    if i == row_index:
                        writer.writerow(new_row)
                    else:
                        writer.writerow(row)
            
            # Replace original file
            os.replace(temp_file, csv_file)
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e'''
    
    lines.insert(insert_index, update_method)
    
    with open(file_manager_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ Added update_row method to {file_manager_path}")

def main():
    """Run all fixes"""
    print("🔧 Fixing MALDB issues...")
    
    try:
        fix_crud_py()
        create_join_py()
        add_update_to_file_manager()
        
        print("\n✅ All fixes applied!")
        print("\nNow you can run:")
        print("  1. cd demo && python simple_web.py")
        print("  2. Or: python -m src.main")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()