"""
Table statistics for query optimization
"""
from typing import Dict, Any

class TableStats:
    """Collects statistics about tables"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.row_count = 0
        self.column_stats: Dict[str, Dict] = {}
    
    def update(self, column_values: Dict[str, Any]):
        """Update statistics with new row"""
        self.row_count += 1
        
        for col_name, value in column_values.items():
            if col_name not in self.column_stats:
                self.column_stats[col_name] = {
                    'min': value,
                    'max': value,
                    'distinct_count': 1,
                    'null_count': 0
                }
            else:
                stats = self.column_stats[col_name]
                if value < stats['min']:
                    stats['min'] = value
                if value > stats['max']:
                    stats['max'] = value
    
    def get_selectivity(self, column: str, operator: str, value: Any) -> float:
        """
        Estimate selectivity of a predicate
        
        Returns:
            Estimated fraction of rows that satisfy the predicate (0.0 to 1.0)
        """
        if column not in self.column_stats or self.row_count == 0:
            return 0.5  # Default guess
        
        stats = self.column_stats[column]
        
        if operator == '=':
            # Assume uniform distribution
            return 1.0 / max(stats.get('distinct_count', 10), 10)
        elif operator in ('<', '<=', '>', '>='):
            # Range selectivity
            return 0.3  # Simple estimate
        else:
            return 0.5