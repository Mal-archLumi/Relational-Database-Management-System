# MALDB Web Demo

This is a demonstration web application showcasing the features of MALDB, a minimal RDBMS with column-level encryption.

## Features Demonstrated

1. **Full CRUD Operations**: Create, Read, Update (via INSERT), Delete operations
2. **Column-Level Encryption**: Passwords are automatically encrypted/decrypted
3. **SQL Interface**: Direct SQL execution via API
4. **Constraints**: PRIMARY KEY, UNIQUE constraints enforced
5. **Web Interface**: Modern web interface built with FastAPI

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install -r ../requirements.txt

# Run the demo
python app.py

# Open browser to http://localhost:8080