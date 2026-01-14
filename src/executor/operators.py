"""
Query execution operators
"""
from typing import List, Tuple, Any, Iterator

class Operator:
    """Base class for query operators"""
    def __init__(self):
        self.children = []
    
    def open(self):
        """Initialize operator"""
        for child in self.children:
            child.open()
    
    def next(self) -> Tuple:
        """Get next tuple"""
        raise NotImplementedError
    
    def close(self):
        """Clean up"""
        for child in self.children:
            child.close()

class ScanOperator(Operator):
    """Table scan operator"""
    def __init__(self, table_name: str, rows: List[Tuple]):
        super().__init__()
        self.table_name = table_name
        self.rows = rows
        self.position = 0
    
    def next(self) -> Tuple:
        if self.position < len(self.rows):
            row = self.rows[self.position]
            self.position += 1
            return row
        return None