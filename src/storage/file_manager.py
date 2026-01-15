"""
Simple file storage - using CSV format for now
We'll upgrade to binary later
"""
import csv
import os
import json
from typing import List, Dict, Any

class FileManager:
    """Simple CSV-based storage"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.data_dir = db_file.replace('.maldb', '_data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def table_file(self, table_name: str) -> str:
        """Get CSV file path for a table"""
        return os.path.join(self.data_dir, f"{table_name}.csv")
    
    def schema_file(self, table_name: str) -> str:
        """Get schema file path for a table"""
        return os.path.join(self.data_dir, f"{table_name}_schema.json")
    
    def save_schema(self, table_name: str, schema: Dict):
        """Save table schema to JSON file"""
        with open(self.schema_file(table_name), 'w') as f:
            json.dump(schema, f, indent=2)
    
    def load_schema(self, table_name: str) -> Dict:
        """Load table schema from JSON file"""
        try:
            with open(self.schema_file(table_name), 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None
    
    def insert_row(self, table_name: str, row: List):
        """Insert a row into CSV file"""
        file_path = self.table_file(table_name)
        
        # Create file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w', newline='') as f:
                pass
        
        # Append row to CSV
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def get_all_rows(self, table_name: str) -> List[List]:
        """Get all rows from CSV file"""
        file_path = self.table_file(table_name)
        
        if not os.path.exists(file_path):
            return []
        
        rows = []
        with open(file_path, 'r', newline='') as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
        
        return rows
    
    def update_row(self, table_name: str, row_index: int, new_row: List):
        """Update a specific row in a table"""
        file_path = self.table_file(table_name)
        temp_file = file_path + '.tmp'
        
        try:
            with open(file_path, 'r', newline='') as infile, \
                 open(temp_file, 'w', newline='') as outfile:
                
                writer = csv.writer(outfile)
                reader = csv.reader(infile)
                
                for i, row in enumerate(reader):
                    if i == row_index:
                        writer.writerow(new_row)
                    else:
                        writer.writerow(row)
            
            # Replace original file
            os.replace(temp_file, file_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        return os.path.exists(self.schema_file(table_name))
    
    def delete_row_by_index(self, table_name: str, row_index: int):
        """Delete a row by index"""
        file_path = self.table_file(table_name)
        temp_file = file_path + '.tmp'
        
        try:
            with open(file_path, 'r', newline='') as infile, \
                 open(temp_file, 'w', newline='') as outfile:
                
                writer = csv.writer(outfile)
                reader = csv.reader(infile)
                
                for i, row in enumerate(reader):
                    if i != row_index:
                        writer.writerow(row)
            
            # Replace original file
            os.replace(temp_file, file_path)
            
        except Exception as e:
            # Clean up temp file if it exists
            if os.path.exists(temp_file):
                os.remove(temp_file)
            raise e
    
    def save_all_rows(self, table_name: str, rows: List[List]):
        """Save all rows to CSV file (overwrites existing)"""
        file_path = self.table_file(table_name)
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)