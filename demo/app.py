# demo/app.py - FIXED VERSION
"""
Demo web application using MALDB
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import sys
import os

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Add src to path
sys.path.insert(0, PROJECT_ROOT)

from src.core.database import Database

app = FastAPI(title="MALDB Demo", version="0.1.0")

# Mount static files - use absolute path
static_dir = os.path.join(BASE_DIR, "static")
templates_dir = os.path.join(BASE_DIR, "templates")

app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Templates
templates = Jinja2Templates(directory=templates_dir)

# Database instance - store in demo directory
db_file = os.path.join(BASE_DIR, "demo.maldb")
db = Database(db_file)

@app.on_event("startup")
async def startup():
    """Initialize demo database"""
    try:
        # Create users table if it doesn't exist
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                email VARCHAR(100),
                password TEXT ENCRYPTED,
                age INT,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Create products table
        db.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INT PRIMARY KEY,
                name VARCHAR(100),
                description TEXT,
                price DECIMAL(10,2),
                category VARCHAR(50),
                in_stock BOOLEAN DEFAULT TRUE
            )
        """)
        
        print("✅ Demo database initialized")
        print(f"📁 Database file: {db_file}")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize demo database: {e}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page"""
    try:
        # Get some stats
        users = db.execute("SELECT * FROM users")
        products = db.execute("SELECT * FROM products")
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user_count": len(users),
            "product_count": len(products)
        })
    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "user_count": 0,
            "product_count": 0,
            "error": str(e)
        })

@app.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    """List all users"""
    try:
        users = db.execute("SELECT id, username, email, age, is_active FROM users")
        
        return templates.TemplateResponse("users.html", {
            "request": request,
            "users": users,
            "count": len(users)
        })
    except Exception as e:
        # Simple error page
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>{str(e)}</p>
                <a href="/">Back to Home</a>
            </body>
        </html>
        """)

@app.get("/products", response_class=HTMLResponse)
async def list_products(request: Request):
    """List all products"""
    try:
        products = db.execute("SELECT * FROM products")
        
        return templates.TemplateResponse("products.html", {
            "request": request,
            "products": products,
            "count": len(products)
        })
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error</h1>
                <p>{str(e)}</p>
                <a href="/">Back to Home</a>
            </body>
        </html>
        """)

@app.post("/users/add")
async def add_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    age: int = Form(...)
):
    """Add a new user"""
    try:
        # Generate ID
        users = db.execute("SELECT id FROM users")
        user_ids = [user[0] for user in users]
        new_id = max(user_ids) + 1 if user_ids else 1
        
        # Insert user (password will be automatically encrypted)
        db.execute(f"""
            INSERT INTO users (id, username, email, password, age, is_active)
            VALUES ({new_id}, '{username}', '{email}', '{password}', {age}, true)
        """)
        
        return RedirectResponse(url="/users", status_code=303)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Adding User</h1>
                <p>{str(e)}</p>
                <a href="/users">Back to Users</a>
            </body>
        </html>
        """)

@app.post("/products/add")
async def add_product(
    request: Request,
    name: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category: str = Form(...)
):
    """Add a new product"""
    try:
        # Generate ID
        products = db.execute("SELECT id FROM products")
        product_ids = [product[0] for product in products]
        new_id = max(product_ids) + 1 if product_ids else 1
        
        db.execute(f"""
            INSERT INTO products (id, name, description, price, category, in_stock)
            VALUES ({new_id}, '{name}', '{description}', {price}, '{category}', true)
        """)
        
        return RedirectResponse(url="/products", status_code=303)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>Error Adding Product</h1>
                <p>{str(e)}</p>
                <a href="/products">Back to Products</a>
            </body>
        </html>
        """)

@app.get("/api/execute")
async def execute_sql(sql: str):
    """Execute raw SQL (for demo purposes)"""
    try:
        result = db.execute(sql)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "maldb-demo"}

@app.get("/api/tables")
async def list_tables():
    """List all tables"""
    try:
        # Simple approach: try to select from known tables
        tables = []
        for table_name in ['users', 'products']:
            try:
                db.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                tables.append(table_name)
            except:
                pass
        return {"tables": tables}
    except Exception as e:
        return {"tables": [], "error": str(e)}

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting MALDB Demo Web Application")
    print("=" * 60)
    print(f"📁 Database: {db_file}")
    print("🌐 Web interface: http://localhost:8080")
    print("📚 API documentation: http://localhost:8080/docs")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8080)