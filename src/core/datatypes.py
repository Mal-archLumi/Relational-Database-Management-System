"""
Simple data types for our database
"""

class DataType:
    """Base class for data types"""
    def validate(self, value):
        raise NotImplementedError

class IntegerType(DataType):
    def validate(self, value):
        return int(value)
    
    def __repr__(self):
        return "INT"

class StringType(DataType):
    def __init__(self, max_length=255):
        self.max_length = max_length
    
    def validate(self, value):
        value = str(value)
        if len(value) > self.max_length:
            raise ValueError(f"String too long (max {self.max_length})")
        return value
    
    def __repr__(self):
        return f"VARCHAR({self.max_length})"

class BooleanType(DataType):
    def validate(self, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    
    def __repr__(self):
        return "BOOLEAN"

# Type mapping
TYPE_MAP = {
    'INT': IntegerType(),
    'INTEGER': IntegerType(),
    'VARCHAR': StringType(),
    'STRING': StringType(),
    'TEXT': StringType(max_length=65535),
    'BOOLEAN': BooleanType(),
    'BOOL': BooleanType(),
}