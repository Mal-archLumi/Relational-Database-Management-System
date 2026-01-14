# MALDB - A Minimal RDBMS with Column-Level Encryption

**MALDB** is a from-scratch relational database management system built in Python, featuring:
- SQL-like query language with REPL interface
- Column-level AES-GCM encryption (creative standout feature)
- Write-Ahead Logging for crash recovery
- B-tree indexing and query optimization hints
- REST API for modern application integration

## 🚀 Features

### Core RDBMS Features
- **SQL Support**: CREATE TABLE, SELECT, INSERT, UPDATE, DELETE, JOIN
- **Data Types**: INT, VARCHAR, BOOLEAN, DECIMAL, TEXT
- **Constraints**: PRIMARY KEY, UNIQUE
- **Indexing**: B-tree indexes for fast lookups
- **Transactions**: BEGIN, COMMIT, ROLLBACK with WAL

### Standout Features ⭐
1. **Column-Level Encryption**: Mark sensitive columns as ENCRYPTED
2. **Query Plan Visualization**: EXPLAIN command with ASCII visualization
3. **Index Advisor**: Suggests indexes based on query patterns
4. **Dual Interface**: SQL REPL + REST API

## 📦 Installation

```bash
git clone https://github.com/Mal-archLumi/Relational-Database-Management-System.git
cd Relational-Database-Management-System
pip install -r requirements.txt

# Set encryption key (optional)
export MALDB_MASTER_KEY="your-32-byte-key-here"