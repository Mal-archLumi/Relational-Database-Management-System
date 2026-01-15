"""
Simple schema manager
"""
from typing import Dict, List, Any
from ..core.datatypes import TYPE_MAP

class Column:
    """Represents a database column"""
    
    def __init__(self, name: str, dtype_str: str):
        self.name = name
        self.dtype_str = dtype_str.upper()
        
        # Parse type (e.g., "VARCHAR(255)" -> StringType(255))
        if '(' in self.dtype_str:
            type_name, rest = self.dtype_str.split('(', 1)
            params = rest.rstrip(')').split(',')
            if type_name == 'VARCHAR':
                # Create a new StringType instance for each column
                from ..core.datatypes import StringType
                max_length = int(params[0].strip())
                self.dtype = StringType(max_length=max_length)
            else:
                self.dtype = TYPE_MAP.get(type_name, TYPE_MAP['VARCHAR'])
        else:
            self.dtype = TYPE_MAP.get(self.dtype_str, TYPE_MAP['VARCHAR'])
        
        # Constraints
        self.primary_key = False
        self.unique = False
        self.not_null = False
        self.encrypted = False
    
    def validate(self, value):
        """Validate and convert value to correct type"""
        if value is None:
            if self.not_null:
                raise ValueError(f"Column {self.name} cannot be NULL")
            return None
        return self.dtype.validate(value)
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'dtype': self.dtype_str,
            'primary_key': self.primary_key,
            'unique': self.unique,
            'not_null': self.not_null,
            'encrypted': self.encrypted
        }

class TableSchema:
    """Represents a database table schema"""
    
    def __init__(self, name: str):
        self.name = name
        self.columns: Dict[str, Column] = {}
        self.primary_key: str = None
    
    def add_column(self, column: Column):
        """Add a column to the table"""
        self.columns[column.name] = column
        
        # Set primary key
        if column.primary_key:
            if self.primary_key and self.primary_key != column.name:
                raise ValueError("Only one primary key allowed per table")
            self.primary_key = column.name
    
    def get_column_names(self) -> List[str]:
        """Get list of column names in order"""
        return list(self.columns.keys())
    
    def validate_row(self, values: List, column_names: List[str] = None) -> List:
        """
        Validate a row against schema
        
        Args:
            values: List of values in column order
            column_names: Optional list of column names for partial inserts
            
        Returns:
            Validated values
        """
        if column_names is None:
            column_names = self.get_column_names()
        
        if len(values) != len(column_names):
            raise ValueError(f"Expected {len(column_names)} values, got {len(values)}")
        
        validated = []
        for col_name, value in zip(column_names, values):
            col = self.columns[col_name]
            validated.append(col.validate(value))
        
        return validated
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'columns': {name: col.to_dict() for name, col in self.columns.items()},
            'primary_key': self.primary_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        table = cls(data['name'])
        
        for col_name, col_data in data['columns'].items():
            col = Column(col_name, col_data['dtype'])
            col.primary_key = col_data['primary_key']
            col.unique = col_data['unique']
            col.not_null = col_data['not_null']
            col.encrypted = col_data['encrypted']
            table.add_column(col)
        
        return table

class Catalog:
    """Manages all table schemas"""
    
    def __init__(self):
        self.tables: Dict[str, TableSchema] = {}
    
    def create_table(self, table_name: str, columns: List[Column]):
        """Create a new table"""
        if table_name in self.tables:
            raise ValueError(f"Table '{table_name}' already exists")
        
        table = TableSchema(table_name)
        for col in columns:
            table.add_column(col)
        
        self.tables[table_name] = table
        return table
    
    def get_table(self, table_name: str) -> TableSchema:
        """Get table schema"""
        if table_name not in self.tables:
            raise ValueError(f"Table '{table_name}' does not exist")
        return self.tables[table_name]
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        return table_name in self.tables