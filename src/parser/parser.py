"""
Enhanced SQL parser with better error handling and constraint parsing
"""
import re
from typing import List, Tuple, Dict, Any
from ..catalog.schema import Column
from ..core.exceptions import ParseError

class SimpleParser:
    """Parses basic SQL statements with better error handling"""
    
    def parse(self, sql: str) -> Dict:
        """
        Parse SQL statement into command dictionary
        
        Returns:
            Dictionary with 'command', 'table', and other relevant info
        """
        # Clean the SQL
        sql = self._clean_sql(sql)
        
        if not sql:
            raise ParseError("Empty SQL statement")
        
        # Convert to uppercase for command detection
        upper_sql = sql.upper()
        
        try:
            if upper_sql.startswith('CREATE TABLE'):
                return self._parse_create_table(sql)
            elif upper_sql.startswith('INSERT INTO'):
                return self._parse_insert(sql)
            elif upper_sql.startswith('SELECT'):
                return self._parse_select(sql)
            elif upper_sql.startswith('UPDATE'):
                return self._parse_update(sql)
            elif upper_sql.startswith('DELETE FROM'):
                return self._parse_delete(sql)
            elif upper_sql.startswith('DROP TABLE'):
                return self._parse_drop_table(sql)
            elif upper_sql.startswith('EXPLAIN'):
                return self._parse_explain(sql)
            elif upper_sql.startswith('HELP'):
                return {'command': 'HELP'}
            else:
                raise ParseError(f"Unsupported SQL command. Try: CREATE TABLE, INSERT, SELECT, UPDATE, DELETE, DROP TABLE")
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(f"SQL parsing error: {str(e)}")
    
    def _clean_sql(self, sql: str) -> str:
        """Clean SQL string - remove comments, extra spaces, etc."""
        # Remove SQL comments (-- comment)
        lines = []
        for line in sql.split('\n'):
            # Remove inline comments
            if '--' in line:
                line = line.split('--')[0]
            lines.append(line.strip())
        
        cleaned = ' '.join(lines).strip()
        
        # Remove trailing semicolon
        if cleaned.endswith(';'):
            cleaned = cleaned[:-1].strip()
        
        # Handle multiple commands separated by semicolons
        if ';' in cleaned:
            # For now, just take the first command
            cleaned = cleaned.split(';')[0].strip()
        
        return cleaned
    
    def _parse_create_table(self, sql: str) -> Dict:
        """
        Parse CREATE TABLE statement with better constraint handling
        
        Format: CREATE TABLE table_name (col1 TYPE constraints, col2 TYPE constraints, ...)
        """
        # Match CREATE TABLE pattern
        pattern = r'CREATE\s+TABLE\s+(\w+)\s*\((.*)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            raise ParseError("Invalid CREATE TABLE syntax. Format: CREATE TABLE name (col1 TYPE, col2 TYPE, ...)")
        
        table_name = match.group(1).strip()
        columns_str = match.group(2).strip()
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        if not columns_str:
            raise ParseError("Table must have at least one column")
        
        # Parse column definitions
        columns = []
        col_defs = self._split_column_definitions(columns_str)
        
        if not col_defs:
            raise ParseError("No valid column definitions found")
        
        for col_def in col_defs:
            col_def = col_def.strip()
            if not col_def:
                continue
            
            try:
                column = self._parse_column_definition(col_def)
                columns.append(column)
            except Exception as e:
                raise ParseError(f"Error parsing column '{col_def}': {e}")
        
        if not columns:
            raise ParseError("No valid columns parsed")
        
        return {
            'command': 'CREATE_TABLE',
            'table': table_name,
            'columns': columns
        }
    
    def _parse_column_definition(self, col_def: str) -> Column:
        """Parse a single column definition with constraints"""
        # Tokenize the column definition
        tokens = []
        current = []
        in_quotes = False
        quote_char = None
        paren_depth = 0  # FIXED: Initialize paren_depth here
        
        for char in col_def:
            if char in ('\'', '"') and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                current.append(char)
            elif char == '(' and not in_quotes:
                paren_depth += 1
                current.append(char)
            elif char == ')' and not in_quotes:
                paren_depth -= 1
                current.append(char)
            elif char == ' ' and not in_quotes and paren_depth == 0:
                if current:
                    tokens.append(''.join(current))
                    current = []
            else:
                current.append(char)
        
        if current:
            tokens.append(''.join(current))
        
        if len(tokens) < 2:
            raise ParseError(f"Invalid column definition: {col_def}")
        
        # First token is column name
        col_name = tokens[0]
        
        # Find data type (could be multiple tokens like "VARCHAR(255)")
        dtype_parts = []
        i = 1
        while i < len(tokens):
            token = tokens[i]
            dtype_parts.append(token)
            # Stop when we hit a constraint keyword or end of tokens
            if i + 1 < len(tokens) and tokens[i + 1].upper() in ('PRIMARY', 'UNIQUE', 'NOT', 'ENCRYPTED', 'CHECK', 'DEFAULT'):
                break
            # Also stop if next token looks like another column constraint
            if i + 1 < len(tokens) and tokens[i + 1].upper() in ('KEY', 'NULL'):
                i += 1
                continue
            i += 1
        
        col_type = ' '.join(dtype_parts)
        
        # Create column
        column = Column(col_name, col_type)
        
        # Parse remaining constraints
        while i < len(tokens):
            token = tokens[i].upper()
            
            if token == 'PRIMARY':
                if i + 1 < len(tokens) and tokens[i + 1].upper() == 'KEY':
                    column.primary_key = True
                    i += 2
                else:
                    i += 1
            elif token == 'UNIQUE':
                column.unique = True
                i += 1
            elif token == 'NOT':
                if i + 1 < len(tokens) and tokens[i + 1].upper() == 'NULL':
                    column.not_null = True
                    i += 2
                else:
                    i += 1
            elif token == 'ENCRYPTED':
                column.encrypted = True
                i += 1
            else:
                i += 1
        
        return column
    
    def _split_column_definitions(self, columns_str: str) -> List[str]:
        """Split column definitions, handling parentheses and nested commas"""
        columns = []
        current = []
        paren_depth = 0
        char_index = 0
        
        while char_index < len(columns_str):
            char = columns_str[char_index]
            
            if char == '(':
                paren_depth += 1
                current.append(char)
            elif char == ')':
                paren_depth -= 1
                current.append(char)
            elif char == ',' and paren_depth == 0:
                # End of column definition
                col_def = ''.join(current).strip()
                if col_def:
                    columns.append(col_def)
                current = []
            else:
                current.append(char)
            
            char_index += 1
        
        # Last column definition
        if current:
            col_def = ''.join(current).strip()
            if col_def:
                columns.append(col_def)
        
        return columns
    
    def _parse_insert(self, sql: str) -> Dict:
        """
        Parse INSERT statement
        
        Format: INSERT INTO table_name VALUES (val1, val2, ...)
        Note: Only handles one INSERT at a time
        """
        # Match INSERT pattern
        pattern = r'INSERT\s+INTO\s+(\w+)\s+VALUES\s*\((.*)\)'
        match = re.match(pattern, sql, re.IGNORECASE | re.DOTALL)
        
        if not match:
            # Also support INSERT INTO table (col1, col2) VALUES (val1, val2)
            pattern2 = r'INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s+VALUES\s*\(([^)]+)\)'
            match = re.match(pattern2, sql, re.IGNORECASE | re.DOTALL)
            if match:
                table_name = match.group(1).strip()
                columns_str = match.group(2).strip()
                values_str = match.group(3).strip()
                
                columns = [col.strip() for col in columns_str.split(',')]
                values = self._parse_values(values_str)
                
                if len(columns) != len(values):
                    raise ParseError(f"Number of columns ({len(columns)}) doesn't match number of values ({len(values)})")
                
                return {
                    'command': 'INSERT',
                    'table': table_name,
                    'columns': columns,
                    'values': values
                }
            
            raise ParseError("Invalid INSERT syntax. Use: INSERT INTO table VALUES (...) or INSERT INTO table (col1, col2) VALUES (val1, val2)")
        
        table_name = match.group(1).strip()
        values_str = match.group(2).strip()
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        # Parse values
        values = self._parse_values(values_str)
        
        return {
            'command': 'INSERT',
            'table': table_name,
            'values': values
        }
    
    def _parse_select(self, sql: str) -> Dict:
        """
        Parse SELECT statement
        
        Format: SELECT * FROM table_name
        Format: SELECT col1, col2 FROM table_name
        """
        # Check for JOIN
        if 'JOIN' in sql.upper():
            return self._parse_join(sql)
        
        # Match SELECT pattern
        pattern = r'SELECT\s+(.+?)\s+FROM\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid SELECT syntax. Format: SELECT column1, column2 FROM table")
        
        columns_str = match.group(1).strip()
        table_name = match.group(2).strip()
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        # Parse column list
        if columns_str.strip() == '*':
            columns = ['*']
        else:
            columns = [col.strip() for col in columns_str.split(',')]
            if not all(columns):
                raise ParseError("Invalid column list")
        
        # Check for WHERE clause
        where_clause = None
        if 'WHERE' in sql.upper():
            where_match = re.search(r'WHERE\s+(.+)$', sql, re.IGNORECASE)
            if where_match:
                where_clause = where_match.group(1).strip()
        
        return {
            'command': 'SELECT',
            'table': table_name,
            'columns': columns,
            'where': where_clause
        }
    
    def _parse_update(self, sql: str) -> Dict:
        """
        Parse UPDATE statement
        
        Format: UPDATE table_name SET col1 = val1, col2 = val2 WHERE condition
        """
        # Match UPDATE pattern
        pattern = r'UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid UPDATE syntax. Format: UPDATE table SET column = value WHERE condition")
        
        table_name = match.group(1).strip()
        set_clause = match.group(2).strip()
        where_clause = match.group(3).strip() if match.group(3) else None
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        # Parse SET clause
        set_parts = {}
        assignments = [a.strip() for a in set_clause.split(',')]
        
        for assignment in assignments:
            if '=' not in assignment:
                raise ParseError(f"Invalid assignment: {assignment}. Use: column = value")
            
            col_name, value_str = assignment.split('=', 1)
            col_name = col_name.strip()
            value_str = value_str.strip()
            
            # Parse value
            value = self._parse_value(value_str)
            set_parts[col_name] = value
        
        return {
            'command': 'UPDATE',
            'table': table_name,
            'set_values': set_parts,
            'where': where_clause
        }
    
    def _parse_delete(self, sql: str) -> Dict:
        """
        Parse DELETE statement
        
        Format: DELETE FROM table_name WHERE condition
        """
        # Match DELETE pattern
        pattern = r'DELETE\s+FROM\s+(\w+)(?:\s+WHERE\s+(.+))?$'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid DELETE syntax. Format: DELETE FROM table WHERE condition")
        
        table_name = match.group(1).strip()
        where_clause = match.group(2).strip() if match.group(2) else None
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        return {
            'command': 'DELETE',
            'table': table_name,
            'where': where_clause
        }
    
    def _parse_drop_table(self, sql: str) -> Dict:
        """Parse DROP TABLE statement"""
        pattern = r'DROP\s+TABLE\s+(\w+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid DROP TABLE syntax. Format: DROP TABLE table_name")
        
        table_name = match.group(1).strip()
        
        if not table_name:
            raise ParseError("Table name cannot be empty")
        
        return {
            'command': 'DROP_TABLE',
            'table': table_name
        }
    
    def _parse_explain(self, sql: str) -> Dict:
        """Parse EXPLAIN statement"""
        # Remove EXPLAIN keyword
        explain_sql = sql[7:].strip()
        
        if not explain_sql:
            raise ParseError("EXPLAIN requires a SQL statement")
        
        # Parse the inner SQL
        try:
            inner_parsed = self.parse(explain_sql)
            return {
                'command': 'EXPLAIN',
                'inner_query': inner_parsed
            }
        except Exception as e:
            raise ParseError(f"Error in EXPLAIN statement: {e}")
    
    def _parse_join(self, sql: str) -> Dict:
        """Parse SELECT with JOIN"""
        # Simple pattern for basic JOIN
        pattern = r'SELECT\s+(.+?)\s+FROM\s+(\w+)\s+JOIN\s+(\w+)\s+ON\s+(.+)'
        match = re.match(pattern, sql, re.IGNORECASE)
        
        if not match:
            raise ParseError("Invalid JOIN syntax. Format: SELECT columns FROM table1 JOIN table2 ON condition")
        
        columns_str = match.group(1).strip()
        table1 = match.group(2).strip()
        table2 = match.group(3).strip()
        on_clause = match.group(4).strip()
        
        # Parse column list
        if columns_str.strip() == '*':
            columns = ['*']
        else:
            columns = [col.strip() for col in columns_str.split(',')]
        
        return {
            'command': 'JOIN',
            'columns': columns,
            'table1': table1,
            'table2': table2,
            'on_clause': on_clause
        }
    
    def _parse_values(self, values_str: str) -> List:
        """Parse comma-separated values, handling quoted strings and nested parentheses"""
        values = []
        current = []
        in_quotes = False
        quote_char = None
        paren_depth = 0
        
        i = 0
        while i < len(values_str):
            char = values_str[i]
            
            if char in ('\'', '"') and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                # Check if it's escaped
                if i > 0 and values_str[i-1] == '\\':
                    current.append(char)
                else:
                    in_quotes = False
                    current.append(char)
            elif char == '(' and not in_quotes:
                paren_depth += 1
                current.append(char)
            elif char == ')' and not in_quotes:
                paren_depth -= 1
                current.append(char)
            elif char == ',' and not in_quotes and paren_depth == 0:
                # End of value
                value_str = ''.join(current).strip()
                value = self._parse_value(value_str)
                values.append(value)
                current = []
            else:
                current.append(char)
            
            i += 1
        
        # Last value
        if current:
            value_str = ''.join(current).strip()
            value = self._parse_value(value_str)
            values.append(value)
        
        return values
    
    def _parse_value(self, value_str: str):
        """Parse a single value string into Python type"""
        value_str = value_str.strip()
        
        if not value_str:
            return None
        
        # Check for NULL
        if value_str.upper() == 'NULL':
            return None
        
        # Check for quoted string
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            # Remove quotes
            unquoted = value_str[1:-1]
            # Handle escaped quotes
            unquoted = unquoted.replace("\\'", "'").replace('\\"', '"')
            return unquoted
        
        # Check for boolean
        if value_str.upper() in ('TRUE', 'FALSE'):
            return value_str.upper() == 'TRUE'
        
        # Check for numbers
        try:
            # Try integer first
            return int(value_str)
        except ValueError:
            try:
                # Try float
                return float(value_str)
            except ValueError:
                # Return as string
                return value_str