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
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
import uvicorn
import os
import sys
import json
import time
import glob
import traceback
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from src.core.database import Database

# Database connection manager with multi-database support
class DatabaseManager:
    _instance = None
    _connections: Dict[str, Database] = {}
    _current_db = "default"  # Track current database
    
    @classmethod
    def set_current_db(cls, db_name: str):
        """Set the current database"""
        cls._current_db = db_name
    
    @classmethod
    def get_current_db(cls):
        """Get current database name"""
        return cls._current_db
    
    @classmethod
    def get_db(cls, name="default"):
        """Get or create a database connection"""
        try:
            if name not in cls._connections:
                # Remove .maldb extension if provided
                if name.endswith('.maldb'):
                    name = name[:-6]
                
                db_path = os.path.join(BASE_DIR, f"{name}.maldb")
                print(f"📁 Creating/loading database: {name} at {db_path}")
                cls._connections[name] = Database(db_path)
                print(f"✅ Database '{name}' loaded successfully")
            
            # Update current database
            if name != cls._current_db:
                print(f"🔄 Switching from {cls._current_db} to {name}")
                cls._current_db = name
            
            return cls._connections[name]
        except Exception as e:
            print(f"❌ Error loading database '{name}': {e}")
            traceback.print_exc()
            raise
    
    @classmethod
    def list_databases(cls):
        """List all available databases in the demo directory"""
        databases = []
        pattern = os.path.join(BASE_DIR, "*.maldb")
        
        print(f"🔍 Scanning for database files with pattern: {pattern}")
        
        # Clear any cached file listings
        import glob
        if hasattr(glob, '_cache'):
            glob._cache.clear()
        
        try:
            db_files = glob.glob(pattern)
            print(f"🔍 Found {len(db_files)} .maldb files: {db_files}")
        except Exception as e:
            print(f"❌ Error scanning for database files: {e}")
            db_files = []
        
        # Always include default first
        default_exists = False
        
        for db_file in db_files:
            try:
                db_name = os.path.basename(db_file).replace(".maldb", "")
                print(f"📁 Processing database file: {db_name} ({db_file})")
                
                # Check if file is accessible
                if not os.path.exists(db_file):
                    print(f"⚠️  Database file doesn't exist: {db_file}")
                    continue
                    
                # Get database info
                tables = 0
                # Count tables by checking for schema files
                data_dir = db_file.replace('.maldb', '_data')
                if os.path.exists(data_dir):
                    schema_files = glob.glob(os.path.join(data_dir, "*_schema.json"))
                    tables = len(schema_files)
                    print(f"   Found {tables} tables in {data_dir}")
                else:
                    print(f"   No data directory found for {db_name}")
                
                databases.append({
                    "name": db_name,
                    "path": db_file,
                    "tables": tables,
                    "size": os.path.getsize(db_file) if os.path.exists(db_file) else 0
                })
                
                if db_name == "default":
                    default_exists = True
                    
            except Exception as e:
                print(f"❌ Error processing {db_file}: {e}")
                traceback.print_exc()
        
        print(f"📋 Total databases found: {len(databases)}")
        
        # If we found no databases at all, make sure default exists
        if len(databases) == 0:
            print("⚠️  No databases found, creating default placeholder")
            default_path = os.path.join(BASE_DIR, "default.maldb")
            databases.append({
                "name": "default",
                "path": default_path,
                "tables": 0,
                "size": 0
            })
            default_exists = True
        
        # Make sure default is always first
        if default_exists:
            # Sort: default first, then others alphabetically
            databases.sort(key=lambda x: (x["name"] != "default", x["name"].lower()))
        else:
            # If default doesn't exist in files, add it
            print("➕ Adding default database to list")
            databases.insert(0, {
                "name": "default",
                "path": os.path.join(BASE_DIR, "default.maldb"),
                "tables": 0,
                "size": 0
            })
        
        print(f"✅ Final database list: {[db['name'] for db in databases]}")
        return databases
    
    @classmethod
    def refresh_databases(cls):
        """Refresh the database list by clearing any caches"""
        # Clear any cached glob results
        import glob
        if hasattr(glob, '_cache'):
            glob._cache.clear()
        
        # Also clear any file system caches
        import sys
        if sys.version_info >= (3, 4):
            import importlib
            importlib.invalidate_caches()
    
    @classmethod
    def create_database(cls, name: str):
        """Create a new database"""
        try:
            # Remove .maldb extension if provided
            if name.endswith('.maldb'):
                name = name[:-6]
            
            # Validate name
            if not name.replace('_', '').isalnum():
                return False, "Database name can only contain letters, numbers, and underscores"
            
            if name.lower() == 'default':
                return False, "Cannot create database named 'default'. It already exists."
            
            # Check if database already exists in connections
            if name in cls._connections:
                return False, f"Database '{name}' already loaded in memory"
            
            db_path = os.path.join(BASE_DIR, f"{name}.maldb")
            
            # Check if file already exists
            if os.path.exists(db_path):
                return False, f"Database file '{name}.maldb' already exists"
            
            print(f"🆕 Creating new database: {name} at {db_path}")
            
            try:
                # First, check if default database exists to copy structure
                default_path = os.path.join(BASE_DIR, "default.maldb")
                
                # Create database by initializing it
                print(f"📝 Initializing database '{name}'...")
                db = Database(db_path)
                
                # Force initialization by executing a simple statement
                # This creates the necessary database structure
                try:
                    # Try to create a dummy table to ensure database is properly initialized
                    db.execute("CREATE TABLE __maldb_init_test (id INT PRIMARY KEY)")
                    db.execute("DROP TABLE __maldb_init_test")
                    print(f"✅ Database '{name}' initialized with schema")
                except Exception as init_error:
                    print(f"⚠️  Initialization test failed (might be OK): {init_error}")
                
                # Verify file was created
                if not os.path.exists(db_path):
                    # Create a minimal database file if it wasn't created
                    print(f"⚠️  Database file not created, creating minimal structure...")
                    import pickle
                    # Create a basic database structure
                    minimal_db = {
                        'catalog': {'tables': {}},
                        'metadata': {'created_at': datetime.now().isoformat(), 'name': name}
                    }
                    with open(db_path, 'wb') as f:
                        pickle.dump(minimal_db, f)
                
                # Create data directory if it doesn't exist
                data_dir = db_path.replace('.maldb', '_data')
                if not os.path.exists(data_dir):
                    os.makedirs(data_dir, exist_ok=True)
                    print(f"📁 Created data directory: {data_dir}")
                
                # Store connection
                cls._connections[name] = db
                
                # Force a refresh of the file system
                cls.refresh_databases()
                
                # Verify creation
                if os.path.exists(db_path):
                    file_size = os.path.getsize(db_path)
                    print(f"✅ Database '{name}' created successfully at {db_path}")
                    print(f"📊 File size: {file_size} bytes")
                    
                    # Test the database connection
                    try:
                        test_result = cls.execute_query("SELECT 1", name)
                        if test_result["success"]:
                            print(f"✅ Database '{name}' is functional")
                        else:
                            print(f"⚠️  Database created but test query failed: {test_result['error']}")
                    except Exception as test_error:
                        print(f"⚠️  Database created but test failed: {test_error}")
                    
                    return True, f"Database '{name}' created successfully"
                else:
                    return False, f"Database file was not created at {db_path}"
                    
            except Exception as db_error:
                print(f"❌ Database creation error: {db_error}")
                traceback.print_exc()
                
                # Clean up any partially created files
                if os.path.exists(db_path):
                    try:
                        os.remove(db_path)
                        print(f"🧹 Cleaned up partially created file: {db_path}")
                    except:
                        pass
                
                data_dir = db_path.replace('.maldb', '_data')
                if os.path.exists(data_dir):
                    try:
                        import shutil
                        shutil.rmtree(data_dir)
                        print(f"🧹 Cleaned up data directory: {data_dir}")
                    except:
                        pass
                
                return False, f"Database creation failed: {str(db_error)}"
                
        except Exception as e:
            print(f"❌ Error creating database '{name}': {e}")
            traceback.print_exc()
            return False, f"Error creating database: {str(e)}"
    
    @classmethod
    def delete_database(cls, name: str):
        """Delete a database"""
        try:
            print(f"🗑️ Attempting to delete database: {name}")
            
            # Don't allow deleting current database if it's the only one
            databases = cls.list_databases()
            if len(databases) <= 1 and name == "default":
                return False, "Cannot delete the only database"
            
            # Close connection if open
            if name in cls._connections:
                db = cls._connections[name]
                try:
                    db.close()
                except:
                    pass
                del cls._connections[name]
            
            # Delete database files
            db_path = os.path.join(BASE_DIR, f"{name}.maldb")
            data_dir = db_path.replace('.maldb', '_data')
            
            deleted_files = []
            
            if os.path.exists(db_path):
                os.remove(db_path)
                deleted_files.append(db_path)
                print(f"🗑️ Deleted database file: {db_path}")
            
            # Delete data directory
            if os.path.exists(data_dir):
                import shutil
                shutil.rmtree(data_dir)
                deleted_files.append(data_dir)
                print(f"🗑️ Deleted data directory: {data_dir}")
            
            # Switch to default if deleting current
            if cls._current_db == name:
                cls._current_db = "default"
                # Ensure default exists
                if not os.path.exists(os.path.join(BASE_DIR, "default.maldb")):
                    # Create a fresh default
                    try:
                        db = Database(os.path.join(BASE_DIR, "default.maldb"))
                        cls._connections["default"] = db
                        print(f"🔄 Created new default database")
                    except Exception as e:
                        print(f"⚠️ Could not create new default: {e}")
            
            print(f"✅ Database '{name}' deleted successfully")
            return True, f"Database '{name}' deleted successfully"
        except Exception as e:
            print(f"❌ Error deleting database '{name}': {e}")
            traceback.print_exc()
            return False, f"Error deleting database: {str(e)}"
    
    @classmethod
    def execute_query(cls, sql: str, db_name="default"):
        """Execute SQL query on specified database"""
        try:
            print(f"⚡ Executing SQL on '{db_name}': {sql[:100]}...")
            
            # Get or create database connection
            db = cls.get_db(db_name)
            
            start_time = time.time()
            result = db.execute(sql)
            execution_time = time.time() - start_time
            
            # Format result properly
            formatted_result = []
            affected_rows = 0
            
            if isinstance(result, list):
                formatted_result = result
                affected_rows = len(result)
            elif result is not None:
                formatted_result = [result]
                affected_rows = 1
            
            print(f"✅ Query executed successfully ({execution_time:.3f}s, {affected_rows} rows)")
            
            return {
                "success": True,
                "result": formatted_result,
                "execution_time": round(execution_time * 1000, 2),  # ms
                "affected_rows": affected_rows,
                "columns": cls._extract_columns(formatted_result) if formatted_result else [],
                "database": db_name
            }
        except Exception as e:
            print(f"❌ Query execution failed: {e}")
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0,
                "database": db_name
            }
    
    @classmethod
    def _extract_columns(cls, result):
        """Extract column names from result"""
        if not result:
            return []
        
        if isinstance(result[0], (list, tuple)):
            # Try to get column names from first row if it's a dict
            if result[0] and isinstance(result[0], dict):
                return list(result[0].keys())
            else:
                return [f"Column_{i+1}" for i in range(len(result[0]))]
        elif isinstance(result[0], dict):
            return list(result[0].keys())
        return ["Result"]
    
    @classmethod
    def get_tables(cls, db_name="default"):
        """Get list of all tables in database"""
        try:
            print(f"📊 Getting tables for database: {db_name}")
            db = cls.get_db(db_name)
            
            # Method 1: Check data directory for schema files
            try:
                # Try to access the data directory
                db_path = os.path.join(BASE_DIR, f"{db_name}.maldb")
                data_dir = db_path.replace('.maldb', '_data')
                
                tables = []
                
                if os.path.exists(data_dir):
                    schema_files = glob.glob(os.path.join(data_dir, "*_schema.json"))
                    for schema_file in schema_files:
                        table_name = os.path.basename(schema_file).replace("_schema.json", "")
                        tables.append(table_name)
                
                if tables:
                    print(f"Found {len(tables)} tables in data directory for {db_name}: {tables}")
                    return tables
            except Exception as e:
                print(f"Could not access data directory for {db_name}: {e}")
            
            # Method 2: Try to get from catalog
            try:
                if hasattr(db, 'catalog') and hasattr(db.catalog, 'tables'):
                    tables = list(db.catalog.tables.keys())
                    if tables:
                        print(f"Found {len(tables)} tables in catalog for {db_name}: {tables}")
                        return tables
            except Exception as e:
                print(f"Could not access catalog for {db_name}: {e}")
            
            print(f"No tables found for {db_name}")
            return []
            
        except Exception as e:
            print(f"❌ Error getting tables for {db_name}: {e}")
            traceback.print_exc()
            return []
    
    @classmethod
    def get_table_schema(cls, table_name: str, db_name="default"):
        """Get schema for a specific table"""
        try:
            print(f"📋 Getting schema for table: {db_name}.{table_name}")
            
            # Method 1: Read schema from file
            try:
                db_path = os.path.join(BASE_DIR, f"{db_name}.maldb")
                data_dir = db_path.replace('.maldb', '_data')
                schema_file = os.path.join(data_dir, f"{table_name}_schema.json")
                
                if os.path.exists(schema_file):
                    with open(schema_file, 'r') as f:
                        schema_data = json.load(f)
                    
                    # Convert to consistent format
                    schema = []
                    if 'columns' in schema_data:
                        for col_name, col_info in schema_data['columns'].items():
                            # Fix: Get proper dtype from the schema
                            dtype_str = col_info.get('dtype_str', col_info.get('dtype', 'VARCHAR'))
                            
                            # Check if it's actually an INT or other type
                            if dtype_str.startswith('INT'):
                                actual_type = 'INT'
                            elif dtype_str.startswith('VARCHAR'):
                                # Extract length if available
                                if '(' in dtype_str:
                                    actual_type = dtype_str
                                else:
                                    actual_type = 'VARCHAR(255)'
                            elif dtype_str.startswith('TEXT'):
                                actual_type = 'TEXT'
                            elif dtype_str.startswith('DECIMAL'):
                                actual_type = 'DECIMAL(10,2)'
                            elif dtype_str.startswith('BOOLEAN') or dtype_str.startswith('BOOL'):
                                actual_type = 'BOOLEAN'
                            else:
                                actual_type = dtype_str
                            
                            schema.append({
                                "name": col_name,
                                "type": actual_type,
                                "primary_key": col_info.get('primary_key', False),
                                "unique": col_info.get('unique', False),
                                "nullable": not col_info.get('not_null', False),
                                "encrypted": col_info.get('encrypted', False),
                                "default": col_info.get('default')
                            })
                        print(f"✅ Got schema from file: {len(schema)} columns")
                        return schema
            except Exception as e:
                print(f"Could not read schema file for {db_name}.{table_name}: {e}")
            
            # Method 2: Try to get from catalog
            try:
                db = cls.get_db(db_name)
                if hasattr(db, 'catalog') and table_name in db.catalog.tables:
                    table = db.catalog.tables[table_name]
                    schema = []
                    for col_name, col in table.columns.items():
                        schema.append({
                            "name": col_name,
                            "type": str(col.dtype) if hasattr(col, 'dtype') else col.dtype_str,
                            "primary_key": col.primary_key,
                            "unique": col.unique,
                            "nullable": not col.not_null,
                            "encrypted": col.encrypted,
                            "default": None
                        })
                    print(f"✅ Got schema from catalog: {len(schema)} columns")
                    return schema
            except Exception as e:
                print(f"Could not get schema from catalog for {db_name}.{table_name}: {e}")
            
            print(f"❌ No schema found for {db_name}.{table_name}")
            return []
            
        except Exception as e:
            print(f"❌ Error getting schema for {db_name}.{table_name}: {e}")
            traceback.print_exc()
            return []

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
    print("🚀 Starting MALDB Interface...")
    
    # Initialize default database with sample data
    try:
        print("📁 Initializing default database...")
        
        # First, list existing databases
        databases = DatabaseManager.list_databases()
        print(f"📋 Found {len(databases)} database(s): {[db['name'] for db in databases]}")
        
        # Get default database (will create if doesn't exist)
        db = DatabaseManager.get_db("default")
        
        # First check what tables already exist
        existing_tables = DatabaseManager.get_tables("default")
        print(f"📊 Existing tables in default: {existing_tables}")
        
        # Create sample tables if they don't exist
        sample_tables = [
            ("users", "CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR(50), email VARCHAR(100), password TEXT ENCRYPTED, age INT, is_active BOOLEAN)"),
            ("products", "CREATE TABLE products (id INT PRIMARY KEY, name VARCHAR(100), description TEXT, price DECIMAL(10,2), category VARCHAR(50), in_stock BOOLEAN)"),
            ("orders", "CREATE TABLE orders (id INT PRIMARY KEY, user_id INT, product_id INT, quantity INT, total DECIMAL(10,2), status VARCHAR(20))")
        ]
        
        for table_name, sql in sample_tables:
            if table_name not in existing_tables:
                try:
                    print(f"🆕 Creating table: {table_name}")
                    result = db.execute(sql)
                    print(f"✅ Created table: {table_name}")
                except Exception as e:
                    print(f"⚠️ Could not create table {table_name}: {e}")
            else:
                print(f"📋 Table already exists: {table_name}")
        
        # Insert some sample data if tables are empty
        for table_name, _ in sample_tables:
            try:
                # Instead of SELECT COUNT(*), try to select all and check length
                # This works because the database doesn't support COUNT(*)
                result = db.execute(f"SELECT * FROM {table_name}")
                
                count = 0
                if result:
                    count = len(result)
                
                if count == 0:
                    # Table is empty, insert sample data
                    if table_name == "users":
                        insert_sql = [
                            "INSERT INTO users VALUES (1, 'alice', 'alice@example.com', 'secret123', 25, true)",
                            "INSERT INTO users VALUES (2, 'bob', 'bob@company.com', 'mypassword', 30, true)"
                        ]
                    elif table_name == "products":
                        insert_sql = [
                            "INSERT INTO products VALUES (1, 'Laptop', 'High-performance laptop', 999.99, 'Electronics', true)",
                            "INSERT INTO products VALUES (2, 'Mouse', 'Wireless mouse', 29.99, 'Electronics', true)"
                        ]
                    elif table_name == "orders":
                        insert_sql = [
                            "INSERT INTO orders VALUES (1, 1, 1, 2, 1999.98, 'completed')",
                            "INSERT INTO orders VALUES (2, 2, 2, 1, 29.99, 'pending')"
                        ]
                    
                    for sql in insert_sql:
                        try:
                            db.execute(sql)
                            print(f"✅ Inserted sample data into {table_name}")
                        except Exception as e:
                            print(f"⚠️ Could not insert into {table_name}: {e}")
                else:
                    print(f"📊 {table_name} already has {count} rows")
            except Exception as e:
                print(f"⚠️ Could not check/insert data for {table_name}: {e}")
                
        print("✅ Database initialization complete")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        traceback.print_exc()
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    # Close all database connections
    for name, db in DatabaseManager._connections.items():
        try:
            db.close()
            print(f"Closed connection to {name}")
        except:
            pass

# Create FastAPI app with documentation enabled
app = FastAPI(
    title="MALDB Interface",
    description="A minimal RDBMS with column-level encryption",
    version="1.0.0",
    docs_url="/api/docs",  # Explicitly set docs URL
    redoc_url="/api/redoc",  # Explicitly set redoc URL
    openapi_url="/api/openapi.json",  # Explicitly set OpenAPI URL
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
    # Get current database and all databases
    current_db = DatabaseManager.get_current_db()
    databases = DatabaseManager.list_databases()
    tables = DatabaseManager.get_tables(current_db)
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "tables": tables,
        "databases": databases,
        "current_db": current_db
    })

@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Custom Swagger UI endpoint"""
    return get_swagger_ui_html(
        openapi_url="/api/openapi.json",
        title="MALDB API Documentation",
        swagger_ui_parameters={"syntaxHighlight.theme": "monokai"}
    )

@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc documentation endpoint"""
    return get_redoc_html(
        openapi_url="/api/openapi.json",
        title="MALDB API Documentation"
    )

@app.post("/api/execute")
async def api_execute(request: Request):
    """Execute SQL query"""
    try:
        data = await request.json()
        sql = data.get("sql", "").strip()
        db_name = data.get("database", DatabaseManager.get_current_db())
        
        if not sql:
            return JSONResponse({
                "success": False,
                "error": "No SQL query provided"
            }, status_code=400)
        
        print(f"🌐 API: Executing SQL on {db_name}")
        result = DatabaseManager.execute_query(sql, db_name)
        
        # Update table list after certain operations
        sql_upper = sql.upper()  # FIXED: Changed toUpperCase() to upper()
        if sql_upper.startswith("CREATE TABLE") or sql_upper.startswith("DROP TABLE"):
            # Refresh table list
            tables = DatabaseManager.get_tables(db_name)
            result["tables_updated"] = tables
        
        return JSONResponse(result)
    except Exception as e:
        print(f"❌ API Execute Error: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/tables")
async def api_tables():
    """List all tables in current database"""
    try:
        current_db = DatabaseManager.get_current_db()
        print(f"🌐 API /api/tables for {current_db}")
        tables = DatabaseManager.get_tables(current_db)
        print(f"📊 API returning tables for {current_db}: {tables}")
        return JSONResponse({
            "success": True,
            "tables": tables,
            "database": current_db
        })
    except Exception as e:
        print(f"❌ API Tables Error: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tables": [],
            "database": "unknown"
        }, status_code=500)

@app.get("/api/tables/{db_name}")
async def api_tables_for_db(db_name: str):
    """List all tables in specific database"""
    try:
        print(f"🌐 API /api/tables/{db_name}")
        tables = DatabaseManager.get_tables(db_name)
        return JSONResponse({
            "success": True,
            "tables": tables,
            "database": db_name
        })
    except Exception as e:
        print(f"❌ API Tables Error for {db_name}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tables": [],
            "database": db_name
        }, status_code=500)

@app.get("/api/schema/{table_name}")
async def api_schema(table_name: str):
    """Get table schema"""
    try:
        current_db = DatabaseManager.get_current_db()
        print(f"🌐 API /api/schema/{table_name} for {current_db}")
        schema = DatabaseManager.get_table_schema(table_name, current_db)
        
        return JSONResponse({
            "success": True,
            "table": table_name,
            "schema": schema,
            "database": current_db
        })
    except Exception as e:
        print(f"❌ API Schema Error for {table_name}: {e}")
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.get("/api/databases")
async def api_databases():
    """List all databases"""
    try:
        # Refresh the database list
        DatabaseManager.refresh_databases()
        
        databases = DatabaseManager.list_databases()
        current_db = DatabaseManager.get_current_db()
        print(f"🌐 API /api/databases: {len(databases)} databases, current: {current_db}")
        return JSONResponse({
            "success": True,
            "databases": databases,
            "current": current_db
        })
    except Exception as e:
        print(f"❌ API Databases Error: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e),
            "databases": []
        }, status_code=500)

@app.post("/api/databases/create")
async def api_create_database(request: Request):
    """Create a new database"""
    try:
        data = await request.json()
        db_name = data.get("name", "").strip()
        
        if not db_name:
            return JSONResponse({
                "success": False,
                "error": "No database name provided"
            }, status_code=400)
        
        print(f"🌐 API /api/databases/create: {db_name}")
        success, message = DatabaseManager.create_database(db_name)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": message,
                "database": db_name
            })
        else:
            return JSONResponse({
                "success": False,
                "error": message
            }, status_code=400)
    except Exception as e:
        print(f"❌ API Create Database Error: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.post("/api/databases/switch")
async def api_switch_database(request: Request):
    """Switch to a different database"""
    try:
        data = await request.json()
        db_name = data.get("name", "").strip()
        
        if not db_name:
            return JSONResponse({
                "success": False,
                "error": "No database name provided"
            }, status_code=400)
        
        print(f"🌐 API /api/databases/switch: {db_name}")
        
        # Get the database (this will create it if needed)
        try:
            db = DatabaseManager.get_db(db_name)
            DatabaseManager.set_current_db(db_name)
            
            # Get tables for the new database
            tables = DatabaseManager.get_tables(db_name)
            
            return JSONResponse({
                "success": True,
                "message": f"Switched to database '{db_name}'",
                "database": db_name,
                "tables": tables
            })
        except Exception as e:
            print(f"❌ Error switching to database {db_name}: {e}")
            traceback.print_exc()
            return JSONResponse({
                "success": False,
                "error": f"Could not switch to database '{db_name}': {str(e)}"
            }, status_code=400)
    except Exception as e:
        print(f"❌ API Switch Database Error: {e}")
        traceback.print_exc()
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

@app.delete("/api/databases/{db_name}")
async def api_delete_database(db_name: str):
    """Delete a database"""
    try:
        print(f"🌐 API /api/databases/{db_name} DELETE")
        success, message = DatabaseManager.delete_database(db_name)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": message
            })
        else:
            return JSONResponse({
                "success": False,
                "error": message
            }, status_code=400)
    except Exception as e:
        print(f"❌ API Delete Database Error: {e}")
        traceback.print_exc()
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
        "service": "maldb",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "current_database": DatabaseManager.get_current_db()
    }

@app.get("/api/info")
async def api_info():
    """Get API information"""
    current_db = DatabaseManager.get_current_db()
    databases = DatabaseManager.list_databases()
    
    return {
        "name": "MALDB API",
        "version": "1.0.0",
        "description": "Minimal Relational Database Management System",
        "current_database": current_db,
        "total_databases": len(databases),
        "endpoints": {
            "POST /api/execute": "Execute SQL query",
            "GET /api/tables": "List all tables in current database",
            "GET /api/tables/{db_name}": "List all tables in specific database",
            "GET /api/schema/{table_name}": "Get table schema",
            "GET /api/databases": "List all databases",
            "POST /api/databases/create": "Create new database",
            "POST /api/databases/switch": "Switch database",
            "DELETE /api/databases/{db_name}": "Delete database",
            "GET /api/health": "Health check",
            "GET /api/docs": "API documentation",
            "GET /": "Web interface"
        },
        "features": [
            "SQL CREATE, INSERT, SELECT, UPDATE, DELETE",
            "Column-level AES-GCM encryption",
            "JOIN operations",
            "Constraint enforcement",
            "Single-command SQL parser",
            "Multiple database support"
        ]
    }

def start_web_interface():
    """Start the web interface"""
    print("\n" + "=" * 60)
    print("🚀 MALDB Professional Interface")
    print("=" * 60)
    print("📁 Created by: Mal-archLumi")
    print("🎯 Purpose: Pesapal Junior Developer Challenge 2026")
    print("⭐ Feature: Column-Level AES-GCM Encryption")
    print("⭐ Feature: Multi-Database Support")
    print("=" * 60)
    print("\n🌐 Starting web server...")
    print("📍 Local: http://localhost:8081")
    print("📚 API Docs: http://localhost:8081/api/docs")
    print("📚 ReDoc: http://localhost:8081/api/redoc")
    print("\n💡 Quick Start:")
    print("   1. Open http://localhost:8081 in your browser")
    print("   2. Create a new database using the database selector")
    print("   3. Try these SQL commands (one at a time):")
    print("      CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), password TEXT ENCRYPTED)")
    print("      INSERT INTO users VALUES (1, 'Alice', 'secret123')")
    print("      SELECT * FROM users")
    print("=" * 60)
    print("\n📝 Sample database 'default' is pre-loaded with:")
    print("   • users (with encrypted password column)")
    print("   • products")
    print("   • orders")
    print("=" * 60)
    
    # Check if static files exist
    if not os.path.exists(os.path.join(static_dir, "style.css")):
        print("\n⚠️  WARNING: Static files not found!")
        print("   Creating basic static files...")
        # Create basic static files if they don't exist
        try:
            with open(os.path.join(static_dir, "style.css"), "w") as f:
                f.write("/* Basic styles */")
            with open(os.path.join(static_dir, "script.js"), "w") as f:
                f.write("// Basic script")
        except:
            pass
    
    uvicorn.run(app, host="0.0.0.0", port=8081)

if __name__ == "__main__":
    start_web_interface()