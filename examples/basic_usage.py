#!/usr/bin/env python3
"""
Basic usage example for MALDB
"""
import sys
sys.path.insert(0, '.')

from src.core.database import Database

def main():
    # Create or connect to database
    db = Database("example.maldb")
    
    print("=== MALDB Basic Usage Example ===")
    
    # Create a table with encrypted column
    print("\n1. Creating table with encrypted column...")
    db.execute("""
        CREATE TABLE employees (
            id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(255) UNIQUE,
            salary DECIMAL(10,2),
            ssn TEXT ENCRYPTED,
            department VARCHAR(50)
        )
    """)
    
    # Insert some data
    print("\n2. Inserting data (SSN will be encrypted automatically)...")
    db.execute("""
        INSERT INTO employees VALUES 
        (1, 'Alice Johnson', 'alice@example.com', 75000.00, '123-45-6789', 'Engineering')
    """)
    
    db.execute("""
        INSERT INTO employees VALUES 
        (2, 'Bob Smith', 'bob@example.com', 65000.00, '987-65-4321', 'Marketing')
    """)
    
    db.execute("""
        INSERT INTO employees VALUES 
        (3, 'Charlie Brown', 'charlie@example.com', 80000.00, '456-78-9123', 'Engineering')
    """)
    
    # Query data
    print("\n3. Querying all employees (SSN is automatically decrypted)...")
    employees = db.execute("SELECT id, name, email, salary, department FROM employees")
    
    print(f"\nFound {len(employees)} employees:")
    for emp in employees:
        print(f"  ID: {emp[0]}, Name: {emp[1]}, Email: {emp[2]}, Salary: ${emp[3]:,.2f}, Dept: {emp[4]}")
    
    # Query with specific columns
    print("\n4. Querying specific columns...")
    names = db.execute("SELECT name, department FROM employees WHERE department = 'Engineering'")
    print(f"\nEngineering employees:")
    for name in names:
        print(f"  {name[0]} - {name[1]}")
    
    # Show table info
    print("\n5. Table information:")
    print("   - Employees table has encrypted column: ssn")
    print("   - Automatic encryption/decryption happens transparently")
    
    # Clean up
    db.execute("DROP TABLE employees")
    db.close()
    
    print("\n=== Example completed successfully ===")

if __name__ == "__main__":
    main()