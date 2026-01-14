"""
Abstract Syntax Tree nodes for SQL
"""
from typing import List, Any, Optional

class ASTNode:
    """Base class for AST nodes"""
    pass

class CreateTableNode(ASTNode):
    """CREATE TABLE statement"""
    def __init__(self, table_name: str, columns: List):
        self.table_name = table_name
        self.columns = columns

class InsertNode(ASTNode):
    """INSERT statement"""
    def __init__(self, table_name: str, values: List):
        self.table_name = table_name
        self.values = values

class SelectNode(ASTNode):
    """SELECT statement"""
    def __init__(self, table_name: str, columns: List[str] = None):
        self.table_name = table_name
        self.columns = columns or ['*']