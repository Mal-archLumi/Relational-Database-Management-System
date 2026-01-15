"""
Simple but powerful web interface for MALDB
Demonstrates SQL execution, encryption, and full CRUD
"""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)

from src.core.database import Database

app = FastAPI(title="MALDB Web Interface")

# Initialize database
db = Database(os.path.join(BASE_DIR, "web_demo.maldb"))

def get_html_template(sql="", tables_html="", result_html=""):
    """Generate HTML template with dynamic content"""
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>MALDB Web Interface</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #e6e6e6;
            line-height: 1.6;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        
        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .tagline {{ opacity: 0.9; font-size: 1.1em; }}
        
        .features {{
            background: #162447;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }}
        
        .editor {{
            background: #0f3460;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        textarea {{
            width: 100%;
            height: 150px;
            background: #1f4068;
            color: #e6e6e6;
            border: 2px solid #667eea;
            border-radius: 5px;
            padding: 15px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            resize: vertical;
        }}
        
        button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            margin: 10px 5px;
            transition: all 0.3s ease;
        }}
        button:hover {{ background: #5a67d8; transform: translateY(-2px); }}
        .btn-primary {{ background: #48bb78; }}
        .btn-primary:hover {{ background: #38a169; }}
        .btn-danger {{ background: #f56565; }}
        .btn-danger:hover {{ background: #e53e3e; }}
        
        .result {{
            background: #1f4068;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background: #0f3460;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #1f4068;
        }}
        th {{
            background: #162447;
            color: #667eea;
        }}
        tr:hover {{ background: #1a1a2e; }}
        
        .example-box {{
            background: #162447;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            border-left: 3px solid #48bb78;
        }}
        .example-box code {{
            background: #0f3460;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        
        .encryption-note {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
            font-weight: bold;
        }}
        
        .tables-list {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin: 20px 0;
        }}
        .table-card {{
            background: #0f3460;
            padding: 20px;
            border-radius: 8px;
            min-width: 200px;
            border: 2px solid transparent;
            transition: all 0.3s ease;
        }}
        .table-card:hover {{
            border-color: #667eea;
            transform: translateY(-5px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧠 MALDB Database Interface</h1>
            <p class="tagline">A Minimal RDBMS with Column-Level Encryption • Pesapal Challenge Submission</p>
        </header>
        
        <div class="encryption-note">
            ⭐ UNIQUE FEATURE: Column-level AES-GCM encryption for sensitive data
        </div>
        
        <div class="features">
            <h3>✅ Supported Features:</h3>
            <ul style="margin-left: 20px; margin-top: 10px;">
                <li>CREATE TABLE with constraints (PRIMARY KEY, UNIQUE, NOT NULL)</li>
                <li>INSERT, SELECT, UPDATE, DELETE operations</li>
                <li>Column-level encryption (mark columns as ENCRYPTED)</li>
                <li>WHERE clause filtering</li>
                <li>Multiple data types: INT, VARCHAR, TEXT, BOOLEAN, DECIMAL</li>
            </ul>
        </div>
        
        <div class="editor">
            <h3>📝 SQL Editor:</h3>
            <form method="post" action="/execute">
                <textarea name="sql" placeholder="Enter SQL command here...">{sql}</textarea>
                <div style="margin-top: 15px;">
                    <button type="submit">Execute SQL</button>
                    <button type="button" onclick="document.querySelector('textarea').value=''" class="btn-danger">Clear</button>
                </div>
            </form>
        </div>
        
        <div class="tables-list">
            {tables_html}
        </div>
        
        <div class="result">
            <h3>📊 Result:</h3>
            {result_html}
        </div>
        
        <div style="margin-top: 30px;">
            <h3>💡 Quick Examples:</h3>
            
            <div class="example-box">
                <strong>Create table with encryption:</strong><br>
                <code>CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), password TEXT ENCRYPTED, age INT)</code>
            </div>
            
            <div class="example-box">
                <strong>Insert data (password auto-encrypted):</strong><br>
                <code>INSERT INTO users VALUES (1, 'Alice', 'secret123', 25)</code>
            </div>
            
            <div class="example-box">
                <strong>Query data (password auto-decrypted):</strong><br>
                <code>SELECT * FROM users WHERE age > 20</code>
            </div>
            
            <div class="example-box">
                <strong>Check encryption in storage:</strong><br>
                <code>SELECT id, name, password FROM users</code> <em>(password shown as encrypted)</em><br>
                <code>SELECT id, name FROM users</code> <em>(password not included in result)</em>
            </div>
        </div>
    </div>
    
    <script>
        // Focus the textarea on load
        document.addEventListener('DOMContentLoaded', () => {{
            const textarea = document.querySelector('textarea');
            if (textarea) textarea.focus();
        }});
        
        // Quick insert buttons for examples
        function insertExample(example) {{
            document.querySelector('textarea').value = example;
        }}
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main web interface"""
    # Get existing tables
    tables_html = ""
    try:
        # List tables by checking data directory
        import glob
        data_dir = os.path.join(BASE_DIR, "web_demo_data")
        schema_files = glob.glob(os.path.join(data_dir, "*_schema.json"))
        
        for schema_file in schema_files:
            table_name = os.path.split(schema_file)[1].replace("_schema.json", "")
            tables_html += f"""
            <div class="table-card">
                <strong>📊 {table_name}</strong>
                <div style="margin-top: 10px;">
                    <button type="button" onclick="insertExample('SELECT * FROM {table_name}')" style="padding: 5px 10px; font-size: 12px;">
                        SELECT
                    </button>
                    <button type="button" onclick="insertExample('DROP TABLE {table_name}')" style="padding: 5px 10px; font-size: 12px; background: #f56565;">
                        DROP
                    </button>
                </div>
            </div>
            """
    except:
        tables_html = "<p>No tables found. Create one using SQL above!</p>"
    
    html_content = get_html_template(
        sql="",
        tables_html=tables_html,
        result_html="<p>👈 Enter SQL commands above to get started</p>"
    )
    
    return HTMLResponse(html_content)

@app.post("/execute")
async def execute_sql(request: Request, sql: str = Form(...)):
    """Execute SQL command"""
    try:
        if not sql.strip():
            return await home(request)
        
        result = db.execute(sql)
        
        # Format result as HTML
        result_html = f"<p>✅ Query executed successfully</p>"
        
        if result:
            result_html += "<table>"
            
            # Try to get column names
            try:
                # This is a simplification - in real scenario, get from schema
                if "SELECT" in sql.upper() and "FROM" in sql.upper():
                    # Extract column names from SQL
                    parts = sql.upper().split("FROM")[0].replace("SELECT", "").strip()
                    if parts == "*":
                        # We don't know column names for *
                        headers = [f"Column {i+1}" for i in range(len(result[0]))]
                    else:
                        headers = [col.strip() for col in parts.split(",")]
                    result_html += "<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>"
            except:
                pass
            
            for row in result:
                result_html += "<tr>" + "".join(f"<td>{str(cell)}</td>" for cell in row) + "</tr>"
            
            result_html += "</table>"
            result_html += f"<p>📊 {len(result)} row(s) returned</p>"
        else:
            result_html += "<p>✅ Command completed (no rows returned)</p>"
            
    except Exception as e:
        result_html = f"""
        <div style="background: #fed7d7; color: #c53030; padding: 15px; border-radius: 5px; margin: 10px 0;">
            <strong>❌ Error:</strong> {str(e)}
        </div>
        """
    
    # Get tables again for display
    tables_html = ""
    try:
        import glob
        data_dir = os.path.join(BASE_DIR, "web_demo_data")
        schema_files = glob.glob(os.path.join(data_dir, "*_schema.json"))
        
        for schema_file in schema_files:
            table_name = os.path.split(schema_file)[1].replace("_schema.json", "")
            tables_html += f"""
            <div class="table-card">
                <strong>📊 {table_name}</strong>
                <div style="margin-top: 10px;">
                    <button type="button" onclick="insertExample('SELECT * FROM {table_name}')" style="padding: 5px 10px; font-size: 12px;">
                        SELECT
                    </button>
                </div>
            </div>
            """
    except:
        tables_html = "<p>No tables found</p>"
    
    html_content = get_html_template(
        sql=sql,
        tables_html=tables_html,
        result_html=result_html
    )
    
    return HTMLResponse(html_content)

@app.get("/api/execute")
async def api_execute(sql: str):
    """API endpoint for SQL execution"""
    try:
        result = db.execute(sql)
        return JSONResponse({
            "success": True,
            "result": result,
            "row_count": len(result)
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=400)

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy"}

if __name__ == "__main__":
    print("🚀 Starting MALDB Web Interface...")
    print("🌐 Open http://localhost:8080 in your browser")
    print("💡 Try these SQL commands:")
    print("   CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), password TEXT ENCRYPTED, age INT)")
    print("   INSERT INTO users VALUES (1, 'Alice', 'secret123', 25)")
    print("   SELECT * FROM users")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8080)