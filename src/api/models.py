"""
Pydantic models for API requests/responses
"""
from pydantic import BaseModel
from typing import List, Optional, Any

class QueryRequest(BaseModel):
    """Request model for SQL query"""
    sql: str
    params: Optional[List[Any]] = None

class QueryResponse(BaseModel):
    """Response model for query execution"""
    success: bool
    result: Optional[List[List[Any]]] = None
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

class TableInfo(BaseModel):
    """Information about a table"""
    name: str
    columns: List[dict]
    row_count: int

class DatabaseInfo(BaseModel):
    """Information about the database"""
    name: str
    tables: List[TableInfo]
    size_bytes: int