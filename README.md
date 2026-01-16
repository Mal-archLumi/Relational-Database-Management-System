# 🗄️ MALDB

**Minimal Relational Database Management System**

> A lightweight, from-scratch relational database built in Python Jan 2026, with **column-level AES-GCM encryption** as its core differentiator.

MALDB demonstrates how a modern RDBMS works internally — parsing SQL, managing schemas, executing queries, and securely storing sensitive data — without hiding behind heavy abstractions.

---

## ✨ Why MALDB?

Most databases hide the hard parts. MALDB exposes them.

* 🔍 **Built from scratch** — no ORM, no existing DB engines
* 🔐 **Security-first** — column-level encryption by design
* 🧠 **Educational** — clear separation of parser, executor, storage
* ⚡ **Lightweight** — zero external deps for core engine
* 🏆 **Challenge-ready** — purpose-built for Pesapal’s Junior Dev Challenge

---

## 🎯 Features

### Core RDBMS Capabilities

* `CREATE TABLE` with data types:

  * `INT`, `VARCHAR`, `TEXT`, `DECIMAL`, `BOOLEAN`
* Full CRUD support:

  * `INSERT`, `SELECT`, `UPDATE`, `DELETE`
* Constraints:

  * `PRIMARY KEY`, `UNIQUE`
* `INNER JOIN` support
* Interactive SQL REPL
* Simple web application demonstrating all operations

---

### ⭐ Standout Feature: Column-Level Encryption

Security is not an afterthought.

* Columns marked as `ENCRYPTED` are **automatically encrypted at rest**
* Uses **AES-GCM authenticated encryption**
* Per-column derived encryption keys
* Transparent automatic decryption during queries
* Persistent secure key storage via `maldb_key.json`

> If the key file is lost, encrypted data is **permanently unrecoverable**.

---

## 🗂 Project Structure

```
Relational-Database-Management-System/
├── src/                      # Core database engine
│   ├── core/                 # Data types, exceptions, interfaces
│   ├── storage/              # File I/O, WAL, encryption logic ★
│   ├── catalog/              # Schema & metadata management
│   ├── parser/               # SQL parser (single-command)
│   ├── executor/             # Query execution engine
│   ├── api/                  # REST API endpoints
│   └── repl/                 # Interactive SQL shell
├── demo/                     # Web demonstration app
│   ├── app.py                # Main web server
│   ├── static/               # CSS & JavaScript
│   └── templates/            # HTML templates
├── tests/                    # Test suite
│   └── test_fixes.py         # 18/18 integration tests
└── README.md
```

---

## ✅ Prerequisites

* Python **3.8+**
* No external dependencies required for the core database

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Mal-archLumi/Relational-Database-Management-System.git
cd Relational-Database-Management-System

# Optional (only for web demo)
pip install -r requirements.txt
```

---

## 💻 Usage

### 1️⃣ Interactive SQL Shell

```bash
python -m src.main
```

⚠️ **Important**: The SQL parser accepts **one command at a time**.
Multiple statements separated by semicolons are **not supported**.

#### Example Session

```
MALDB> CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(50),
  password TEXT ENCRYPTED,
  age INT
)
✅ Table 'users' created successfully

MALDB> INSERT INTO users VALUES (1, 'Alice', 'secret123', 25)
✅ 1 row inserted

MALDB> SELECT * FROM users
📊 1 row(s) returned:
(1, 'Alice', 'secret123', 25)
```

---

### 2️⃣ Web Application Demo

```bash
cd demo
python app.py
```

Open in browser:

👉 **[http://localhost:8081](http://localhost:8081)**

**Web Demo Features**

* Modern dark UI
* Embedded SQL editor
* Real-time query execution
* Results table rendering
* Table browser & query history

---

## 🔧 Supported SQL Commands (Single-line Only)

```sql
-- CREATE with encryption
CREATE TABLE patients (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  diagnosis TEXT ENCRYPTED
)

-- INSERT (auto-encrypted)
INSERT INTO patients VALUES (101, 'John Doe', 'Hypertension, controlled')

-- SELECT (auto-decrypted)
SELECT * FROM patients WHERE id = 101

-- UPDATE
UPDATE patients SET diagnosis = 'Hypertension, stable' WHERE id = 101

-- DELETE
DELETE FROM patients WHERE id = 101
```

---

## 🧪 Testing

```bash
python tests/test_fixes.py
```

Expected output:

```
18/18 tests passed
```

Test coverage includes:

* CRUD operations
* Constraints
* Encryption & decryption
* JOIN logic
* Error handling

---

## ⚠️ Important Notes

* Only **single SQL commands** are supported per execution
* Encryption key file (`maldb_key.json`) is auto-generated on first run
* **Do not delete or expose the key file** — encrypted data cannot be recovered

---

## 🎯 Demonstration Flow (Recommended)

1. Run `python -m src.main`
2. Create a table with encrypted columns
3. Insert sensitive data
4. Query and observe automatic decryption
5. Launch the web demo (`demo/app.py`)
6. Repeat the same operations via the UI

---

## 📄 License

Project developed for the **Pesapal Junior Developer Challenge 2026**.

---

> **MALDB** — minimal by design, secure by default.
