# MALDB - Minimal Relational Database Management System

A lightweight, from-scratch relational database built in Python for the **Pesapal Junior Developer Challenge 2026**, featuring **column-level AES-GCM encryption** as its primary standout capability.

## 🎯 Features

### Core RDBMS Capabilities
- CREATE TABLE with data types: INT, VARCHAR, TEXT, DECIMAL, BOOLEAN  
- Full CRUD operations: INSERT, SELECT, UPDATE, DELETE  
- Constraints: PRIMARY KEY, UNIQUE  
- INNER JOIN support  
- SQL interface with interactive REPL  
- Simple web application demonstrating all operations  

### ⭐ Standout Feature: Column-Level Encryption
- Columns marked as `ENCRYPTED` are automatically encrypted at rest  
- AES-GCM authenticated encryption with per-column derived keys  
- Transparent automatic decryption during queries  
- Secure key management with file persistence (`maldb_key.json`)

## 📁 Project Structure

Relational-Database-Management-System/
├── src/                    # Core database engine
│   ├── core/              # Data types, exceptions, interface
│   ├── storage/           # File I/O, WAL, encryption logic ★
│   ├── catalog/           # Schema & metadata management
│   ├── parser/            # SQL parser (single command)
│   ├── executor/          # Query execution engine
│   ├── api/               # REST API endpoints
│   └── repl/              # Interactive SQL shell
├── demo/                  # Web demonstration
│   ├── app.py             # Main web application
│   ├── static/            # CSS + JavaScript
│   └── templates/         # HTML templates
├── tests/                 # Test suite
│   └── test_fixes.py      # 18/18 integration tests
└── README.md


## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- No external dependencies required for core functionality

### Installation

```bash
git clone https://github.com/Mal-archLumi/Relational-Database-Management-System.git
cd Relational-Database-Management-System

# Optional: install requirements if you want to run the web demo
pip install -r requirements.txt

💻 Usage
1. Interactive SQL Shell 
Bashpython -m src.main
Important: The parser accepts only one SQL command at a time.
Multiple statements separated by semicolons are not supported.
Example session:

MALDB> CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), password TEXT ENCRYPTED, age INT)
✅ Table 'users' created successfully

MALDB> INSERT INTO users VALUES (1, 'Alice', 'secret123', 25)
✅ 1 row inserted

MALDB> SELECT * FROM users
📊 1 row(s) returned:
  (1, 'Alice', 'secret123', 25)


2. Web Application Demo
cd demo
python app.py

Then open: http://localhost:8081
Features: modern dark theme, SQL editor, real-time results table, table browser, query history

🔧 Supported SQL Commands (Single line commands only) Examples
-- CREATE with encryption
CREATE TABLE patients (id INT PRIMARY KEY, name VARCHAR(100), diagnosis TEXT ENCRYPTED)

-- INSERT (auto-encrypted)
INSERT INTO patients VALUES (101, 'John Doe', 'Hypertension, controlled')

-- SELECT (auto-decrypted)
SELECT * FROM patients WHERE id = 101

-- UPDATE
UPDATE patients SET diagnosis = 'Hypertension, stable' WHERE id = 101

-- DELETE
DELETE FROM patients WHERE id = 101

🧪 Testing
python tests/test_fixes.py

Expected result:
18/18 tests passed
(covers CRUD, constraints, encryption, JOINs, error cases)

⚠️ Important Notes

Single command limitation — execute each statement separately
Encryption key (maldb_key.json) is auto-generated on first run
→ Keep this file secure — encrypted data is unrecoverable without it

🎯 Demonstration Flow 

Run python -m src.main
Create encrypted table
Insert sensitive data
Query → observe automatic decryption
Run the web demo (demo/app.py)
Try the same operations through the beautiful interface

📄 License
Project developed for Pesapal Junior Developer Challenge 2026