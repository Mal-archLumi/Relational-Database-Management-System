"""
Output formatting for SQL results
"""
from tabulate import tabulate
from typing import List, Tuple

def format_results(rows: List[Tuple], headers: List[str] = None) -> str:
    """
    Format query results as a table
    
    Args:
        rows: List of tuples representing rows
        headers: Optional list of column headers
        
    Returns:
        Formatted table string
    """
    if not rows:
        return "No rows found"
    
    if headers is None:
        headers = [f"col{i+1}" for i in range(len(rows[0]))]
    
    return tabulate(rows, headers=headers, tablefmt="grid")

def format_single_value(value) -> str:
    """Format a single value for display"""
    if value is None:
        return "NULL"
    elif isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    elif isinstance(value, (int, float)):
        return str(value)
    else:
        return str(value)