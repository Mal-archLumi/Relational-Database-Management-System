"""
Simple query planner
"""
from typing import List, Dict, Any

class QueryPlanner:
    """Plans query execution (simple for now)"""
    
    def __init__(self, catalog):
        self.catalog = catalog
    
    def create_plan(self, parsed: Dict) -> Dict:
        """
        Create execution plan for query
        
        Returns:
            Plan dictionary
        """
        return parsed  # For now, just pass through