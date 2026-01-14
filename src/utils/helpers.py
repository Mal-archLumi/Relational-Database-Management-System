"""
Helper utilities
"""
import os
import json
from typing import Any, Dict, List

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except:
        return 0

def format_bytes(size: int) -> str:
    """Format bytes to human readable string"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def read_json_file(file_path: str) -> Dict:
    """Read JSON file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}

def write_json_file(file_path: str, data: Dict):
    """Write JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def validate_table_name(name: str) -> bool:
    """Validate table name"""
    if not name:
        return False
    if not name[0].isalpha() and name[0] != '_':
        return False
    if not all(c.isalnum() or c == '_' for c in name):
        return False
    return True

def validate_column_name(name: str) -> bool:
    """Validate column name"""
    return validate_table_name(name)  # Same rules for now