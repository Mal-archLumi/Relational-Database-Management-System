"""
REST API server for MALDB
"""
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any
from ..core.database import Database
from ..core.exceptions import ParseError, ExecutionError
from .models import QueryRequest, QueryResponse, DatabaseInfo, TableInfo

app = FastAPI(title="MALDB API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database instance
db_instance = None

def start_api_server(port: int = 8000, db_file: str = "default.maldb"):
    """Start the API server"""
    import uvicorn
    global db_instance
    
    # Initialize database
    db_instance = Database(db_file)
    
    print(f"Starting MALDB API server on http://localhost:{port}")
    print(f"API documentation: http://localhost:{port}/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    global db_instance
    if db_instance is None:
        db_instance = Database()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_instance
    if db_instance:
        db_instance.close()

@app.post("/api/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a SQL query"""
    global db_instance
    
    if not db_instance:
        return QueryResponse(
            success=False,
            error="Database not initialized",
            execution_time_ms=0
        )
    
    start_time = time.time()
    
    try:
        result = db_instance.execute(request.sql)
        
        # Convert tuples to lists for JSON serialization
        result_list = [list(row) for row in result]
        
        return QueryResponse(
            success=True,
            result=result_list,
            execution_time_ms=(time.time() - start_time) * 1000
        )
        
    except (ParseError, ExecutionError) as e:
        # These are expected errors from invalid SQL
        return QueryResponse(
            success=False,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000
        )
    except Exception as e:
        # Unexpected server errors
        import traceback
        traceback.print_exc()
        return QueryResponse(
            success=False,
            error=f"Internal server error: {str(e)}",
            execution_time_ms=(time.time() - start_time) * 1000
        )

@app.get("/tables", response_model=List[str])
async def list_tables():
    """List all tables in the database"""
    global db_instance
    
    try:
        if not db_instance:
            raise HTTPException(status_code=503, detail="Database not initialized")
        
        tables = list(db_instance.catalog.tables.keys())
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables/{table_name}", response_model=TableInfo)
async def get_table_info(table_name: str):
    """Get information about a specific table"""
    global db_instance
    
    try:
        if not db_instance:
            raise HTTPException(status_code=503, detail="Database not initialized")
        
        if table_name not in db_instance.catalog.tables:
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
        
        table = db_instance.catalog.tables[table_name]
        
        # Get row count
        rows = db_instance.file_manager.get_all_rows(table_name)
        row_count = len(rows)
        
        # Convert columns to dict
        columns = [col.to_dict() for col in table.columns.values()]
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if db_instance:
            return {"status": "healthy", "service": "maldb-api", "tables": len(db_instance.catalog.tables)}
        else:
            return {"status": "starting", "service": "maldb-api"}
    except Exception:
        return {"status": "unhealthy", "service": "maldb-api"}

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "MALDB API",
        "version": "0.1.0",
        "endpoints": {
            "/api/execute": "POST - Execute SQL query",
            "/tables": "GET - List all tables",
            "/tables/{name}": "GET - Get table info",
            "/health": "GET - Health check",
            "/docs": "API documentation"
        }
    }