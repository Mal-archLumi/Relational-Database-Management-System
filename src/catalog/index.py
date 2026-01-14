"""
Simple index implementation
"""
from typing import Dict, List, Any

class Index:
    """Simple hash index for primary keys"""
    
    def __init__(self, column_name: str):
        self.column_name = column_name
        self.index: Dict[Any, int] = {}  # value -> row_position
    
    def insert(self, value: Any, position: int):
        """Add entry to index"""
        self.index[value] = position
    
    def delete(self, value: Any):
        """Remove entry from index"""
        if value in self.index:
            del self.index[value]
    
    def get(self, value: Any) -> int:
        """Get position by value"""
        return self.index.get(value)
    
    def contains(self, value: Any) -> bool:
        """Check if value exists in index"""
        return value in self.index