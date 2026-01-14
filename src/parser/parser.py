"""
Simple SQL parser - handles basic CREATE TABLE and INSERT
"""
import re
from typing import List, Tuple, Dict, Any
from ..catalog.schema import Column
from ..core.exceptions import ParseError

class SimpleParser:
    """Parses basic SQL statements"""
    
    def parse(self, sql: str) -> Dict:
        """
        Parse SQL statement into command dictionary
        
        Returns:
            Dictionary with 'command', 'table', and other relevant info
        """
        sql = sql.strip().rstrip(';')
        
        # Convert to uppercase for command detection
        upper_sql = sql.upper()
        
        if upper_sql.startswith('CREATE TABLE'):
            return self._parse_create_table(sql)
        elif upper_sql.startswith('INSERT INTO'):
            return self._parse_insert(sql)
        elif upper_sql.startswith('SELECT'):
            return self._parse_select(sql)
        elif upper_sql.startswith('DROP TABLE'):
            return self._parse_drop_table(sql)
        else:
            raise ParseError(f"Unsupported SQL command: {sql[:20]}...")
    
    def _parse_create_table(self, sql: str) -> Dict:
        """
        Parse CREATE TABLE statement
        
        Format: CREATE TABLE table_name (col1 TYPE, col2 TYPE, ...)
        """
        # Simple regex parsing
        pattern = r'CREATE TABLE\s+(\w+)\s*\((.*)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ParseError("Invalid CREATE TABLE syntax")
        
        table_name = match.group(1)
        columns_str = match.group(2).strip()
        
        # Parse column definitions
        columns = []
        col_defs = self._split_columns(columns_str)
        
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            
            # Parse column name and type
            parts = col_def.split()
            if len(parts) < 2:
                raise ParseError(f"Invalid column definition: {col_def}")
            
            col_name = parts[0]
            col_type = ' '.join(parts[1:])  # Handle types like "VARCHAR(255)"
            
            # Create column
            column = Column(col_name, col_type)
            
            # Check for constraints
            col_upper = col_def.upper()
            if 'PRIMARY KEY' in col_upper:
                column.primary_key = True
            if 'UNIQUE' in col_upper:
                column.unique = True
            if 'NOT NULL' in col_upper:
                column.not_null = True
            if 'ENCRYPTED' in col_upper:
                column.encrypted = True
            
            columns.append(column)
        
        return {
            'command': 'CREATE_TABLE',
            'table': table_name,
            'columns': columns
        }
    
    def _parse_insert(self, sql: str) -> Dict:
        """
        Parse INSERT statement
        
        Format: INSERT INTO table_name VALUES (val1, val2, ...)
        """
        # Simple regex parsing
        pattern = r'INSERT INTO\s+(\w+)\s+VALUES\s*\((.*)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ParseError("Invalid INSERT syntax. Use: INSERT INTO table VALUES (...)")
        
        table_name = match.group(1)
        values_str = match.group(2)
        
        # Parse values
        values = self._parse_values(values_str)
        
        return {
            'command': 'INSERT',
            'table': table_name,
            'values': values
        }
    
    def _parse_select(self, sql: str) -> Dict:
        """
        Parse basic SELECT statement
        
        Format: SELECT * FROM table_name
        """
        pattern = r'SELECT\s+(.*?)\s+FROM\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            # Try SELECT * FROM table
            pattern2 = r'SELECT\s+\*\s+FROM\s+(\w+)'
            match = re.match(pattern2, sql, re.IGNORECASE)
            if match:
                return {
                    'command': 'SELECT',
                    'table': match.group(1),
                    'columns': ['*']
                }
            raise ParseError("Invalid SELECT syntax")
        
        columns_str = match.group(1)
        table_name = match.group(2)
        
        # Parse column list
        if columns_str.strip() == '*':
            columns = ['*']
        else:
            columns = [col.strip() for col in columns_str.split(',')]
        
        return {
            'command': 'SELECT',
            'table': table_name,
            'columns': columns
        }
    
    def _parse_drop_table(self, sql: str) -> Dict:
        """Parse DROP TABLE statement"""
        pattern = r'DROP TABLE\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid DROP TABLE syntax")
        
        return {
            'command': 'DROP_TABLE',
            'table': match.group(1)
        }
    
    def _split_columns(self, columns_str: str) -> List[str]:
        """Split column definitions, handling parentheses"""
        columns = []
        current = []
        paren_count = 0
        
        for char in columns_str:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == ',' and paren_count == 0:
                columns.append(''.join(current).strip())
                current = []
                continue
            
            current.append(char)
        
        if current:
            columns.append(''.join(current).strip())
        
        return columns
    
    def _parse_values(self, values_str: str) -> List:
        """Parse comma-separated values, handling quoted strings"""
        values = []
        current = []
        in_quote = False
        quote_char = None
        
        for char in values_str:
            if char in ("'", '"') and not in_quote:
                in_quote = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quote:
                in_quote = False
                current.append(char)
            elif char == ',' and not in_quote:
                # End of value
                value_str = ''.join(current).strip()
                values.append(self._parse_value(value_str))
                current = []
            else:
                current.append(char)
        
        # Last value
        if current:
            value_str = ''.join(current).strip()
            values.append(self._parse_value(value_str))
        
        return values
    
    def _parse_value(self, value_str: str):
        """Parse a single value string into Python type"""
        value_str = value_str.strip()
        
        if not value_str:
            return None
        
        # Check for quoted string
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1]
        
        # Check for NULL
        if value_str.upper() == 'NULL':
            return None
        
        # Check for numbers
        try:
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            # Check for boolean
            if value_str.upper() in ('TRUE', 'FALSE'):
                return value_str.upper() == 'TRUE'
            
            # Return as string
            return value_str