# demo/app.py
"""
Professional Web Interface for MALDB RDBMS
Clean, modern, and functional - designed for database professionals
"""
from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys
import json
import time
import glob
from typing import Dict, List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from src.core.database import Database

# Database connection manager
class DatabaseManager:
    _instance = None
    _db = None
    _connections: Dict[str, Database] = {}
    
    @classmethod
    def get_db(cls, name="default"):
        if name not in cls._connections:
            db_path = os.path.join(BASE_DIR, f"professional_{name}.maldb")
            cls._connections[name] = Database(db_path)
        return cls._connections[name]
    
    @classmethod
    def execute_query(cls, sql: str, db_name="default"):
        try:
            db = cls.get_db(db_name)
            start_time = time.time()
            result = db.execute(sql)
            execution_time = time.time() - start_time
            
            # Get affected rows count
            affected_rows = len(result) if isinstance(result, list) else 0
            
            return {
                "success": True,
                "result": result,
                "execution_time": round(execution_time * 1000, 2),  # ms
                "affected_rows": affected_rows,
                "columns": cls._extract_columns(result, sql) if result else []
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0
            }
    
    @classmethod
    def _extract_columns(cls, result, sql):
        """Extract column names from result"""
        if not result:
            return []
        
        if isinstance(result[0], (list, tuple)):
            return [f"Column_{i+1}" for i in range(len(result[0]))]
        elif isinstance(result[0], dict):
            return list(result[0].keys())
        return []
    
    @classmethod
    def get_tables(cls, db_name="default"):
        """Get list of all tables in database"""
        try:
            db = cls.get_db(db_name)
            
            # Check data directory for schema files
            data_dir = db._storage.data_dir
            tables = []
            
            if os.path.exists(data_dir):
                schema_files = glob.glob(os.path.join(data_dir, "*_schema.json"))
                for schema_file in schema_files:
                    table_name = os.path.basename(schema_file).replace("_schema.json", "")
                    tables.append(table_name)
            
            return tables
        except Exception as e:
            print(f"Error getting tables: {e}")
            return []
    
    @classmethod
    def get_table_schema(cls, table_name: str, db_name="default"):
        """Get schema for a specific table"""
        try:
            db = cls.get_db(db_name)
            
            # Read schema from file
            data_dir = db._storage.data_dir
            schema_file = os.path.join(data_dir, f"{table_name}_schema.json")
            
            if not os.path.exists(schema_file):
                return None
            
            with open(schema_file, 'r') as f:
                schema_data = json.load(f)
            
            # Convert to consistent format
            schema = []
            for col_name, col_info in schema_data.get('columns', {}).items():
                schema.append({
                    "name": col_name,
                    "type": col_info.get('type', 'VARCHAR'),
                    "primary_key": col_info.get('primary_key', False),
                    "unique": col_info.get('unique', False),
                    "nullable": col_info.get('nullable', True),
                    "encrypted": col_info.get('encrypted', False),
                    "default": col_info.get('default')
                })
            
            return schema
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return None

# WebSocket manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager"""
    # Startup
    print("🚀 Starting MALDB Professional Interface...")
    
    # Initialize with some sample data - USING SIMPLIFIED SYNTAX FOR MALDB
    try:
        db = DatabaseManager.get_db()
        # Create sample tables if they don't exist - USING MALDB-COMPATIBLE SYNTAX
        sample_tables = [
            # MALDB syntax: CREATE TABLE name (col1 TYPE, col2 TYPE, ...)
            "CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), password TEXT ENCRYPTED, age INT, is_active BOOLEAN)",
            "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100), description TEXT, price DECIMAL(10,2), category VARCHAR(50), in_stock BOOLEAN)",
            "CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, product_id INT, quantity INT, total DECIMAL(10,2), status VARCHAR(20))"
        ]
        
        for sql in sample_tables:
            try:
                db.execute(sql)
                print(f"✅ Created table: {sql.split(' ')[2]}")
            except Exception as e:
                # Table might already exist
                if "already exists" in str(e).lower() or "exists" in str(e).lower():
                    print(f"📋 Table already exists: {sql.split(' ')[2]}")
                else:
                    print(f"Note: Could not create sample table: {e}")
        
        # Insert some sample data
        sample_data = [
            "INSERT INTO users VALUES (1, 'alice', 'alice@example.com', 'secret123', 25, true)",
            "INSERT INTO users VALUES (2, 'bob', 'bob@company.com', 'mypassword', 30, true)",
            "INSERT INTO products VALUES (1, 'Laptop', 'High-performance laptop', 999.99, 'Electronics', true)",
            "INSERT INTO products VALUES (2, 'Mouse', 'Wireless mouse', 29.99, 'Electronics', true)",
            "INSERT INTO orders VALUES (1, 1, 1, 2, 1999.98, 'completed')",
            "INSERT INTO orders VALUES (2, 2, 2, 1, 29.99, 'pending')"
        ]
        
        for sql in sample_data:
            try:
                db.execute(sql)
                print(f"✅ Inserted sample data")
            except Exception as e:
                # Data might already exist
                if "constraint" in str(e).lower():
                    print(f"📋 Data already exists or constraint violation: {e}")
                else:
                    print(f"Note: Could not insert sample data: {e}")
                
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")

app = FastAPI(
    title="MALDB Professional Interface",
    description="A minimal RDBMS with column-level encryption",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create directories if they don't exist
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

# Create directories if they don't exist
os.makedirs(static_dir, exist_ok=True)
os.makedirs(templates_dir, exist_ok=True)

# Mount static files from existing directory
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=templates_dir)

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/execute")
async def api_execute(request: Request):
    """Execute SQL query"""
    try:
        data = await request.json()
        sql = data.get("sql", "").strip()
        db_name = data.get("database", "default")
        
        if not sql:
            return JSONResponse({
                "success": False,
                "error": "No SQL query provided"
            }, status_code=400)
        
        print(f"Executing SQL: {sql}")
        result = DatabaseManager.execute_query(sql, db_name)
        return JSONResponse(result)
    except Exception as e:
        print(f"API Execute Error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/tables")
async def api_tables():
    """List all tables"""
    try:
        tables = DatabaseManager.get_tables("default")
        print(f"Found tables: {tables}")
        return JSONResponse({
            "success": True,
            "tables": tables
        })
    except Exception as e:
        print(f"API Tables Error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tables": []
        }, status_code=500)

@app.get("/api/schema/{table_name}")
async def api_schema(table_name: str):
    """Get table schema"""
    try:
        schema = DatabaseManager.get_table_schema(table_name, "default")
        
        if schema is None:
            # Fallback to sample schema
            schemas = {
                "users": [
                    {"name": "id", "type": "INT", "primary_key": True, "encrypted": False},
                    {"name": "username", "type": "VARCHAR(50)", "unique": True, "encrypted": False},
                    {"name": "email", "type": "VARCHAR(100)", "encrypted": False},
                    {"name": "password", "type": "TEXT", "encrypted": True},
                    {"name": "age", "type": "INT", "encrypted": False},
                    {"name": "is_active", "type": "BOOLEAN", "encrypted": False}
                ],
                "products": [
                    {"name": "id", "type": "INT", "primary_key": True, "encrypted": False},
                    {"name": "name", "type": "VARCHAR(100)", "encrypted": False},
                    {"name": "description", "type": "TEXT", "encrypted": False},
                    {"name": "price", "type": "DECIMAL(10,2)", "encrypted": False},
                    {"name": "category", "type": "VARCHAR(50)", "encrypted": False},
                    {"name": "in_stock", "type": "BOOLEAN", "encrypted": False}
                ],
                "orders": [
                    {"name": "id", "type": "INT", "primary_key": True, "encrypted": False},
                    {"name": "user_id", "type": "INT", "encrypted": False},
                    {"name": "product_id", "type": "INT", "encrypted": False},
                    {"name": "quantity", "type": "INT", "encrypted": False},
                    {"name": "total", "type": "DECIMAL(10,2)", "encrypted": False},
                    {"name": "status", "type": "VARCHAR(20)", "encrypted": False}
                ]
            }
            schema = schemas.get(table_name, [])
        
        return JSONResponse({
            "success": True,
            "table": table_name,
            "schema": schema
        })
    except Exception as e:
        print(f"API Schema Error for {table_name}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "maldb-professional",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

def start_web_interface():
    """Start the professional web interface"""
    print("\n" + "=" * 60)
    print("🚀 MALDB Professional Interface")
    print("=" * 60)
    print("📁 Created by: Mal-archLumi")
    print("🎯 Purpose: Pesapal Junior Developer Challenge 2026")
    print("⭐ Feature: Column-Level AES-GCM Encryption")
    print("=" * 60)
    print("\n🌐 Starting web server...")
    print("📍 Local: http://localhost:8081")
    print("📚 API Docs: http://localhost:8081/api/docs")
    print("\n💡 Quick Start:")
    print("   1. Open http://localhost:8081 in your browser")
    print("   2. Try these SQL commands:")
    print("      CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), password TEXT ENCRYPTED)")
    print("      INSERT INTO users VALUES (1, 'Alice', 'secret123')")
    print("      SELECT * FROM users")
    print("=" * 60)
    print("\n📝 Sample tables are pre-loaded:")
    print("   • users (with encrypted password column)")
    print("   • products")
    print("   • orders")
    print("=" * 60)
    
    # Check if static files exist
    if not os.path.exists(os.path.join(static_dir, "style.css")):
        print("\n⚠️  WARNING: Static files not found!")
        print("   Please create these files manually:")
        print("   - demo/static/style.css")
        print("   - demo/static/script.js")
        print("   - demo/templates/base.html")
        print("   - demo/templates/index.html")
    
    uvicorn.run(app, host="0.0.0.0", port=8081)

if __name__ == "__main__":
    start_web_interface()