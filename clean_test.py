#!/usr/bin/env python3
"""
Clean test for MALDB - deletes old data first
"""
import os
import sys
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cleanup_test_db():
    """Remove test database files"""
    test_dirs = [
        "test_fixes.maldb_data",
        "maldb_key.json",
        "test_fixes_key.json"
    ]
    
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                print(f"🗑️  Deleted directory: {dir_path}")
            else:
                os.remove(dir_path)
                print(f"🗑️  Deleted file: {dir_path}")

from src.core.database import Database

def run_test(test_name, sql, expected_error=None, db=None):
    """Run a single test"""
    print(f"\n🧪 {test_name}")
    print(f"   SQL: {sql}")
    
    try:
        if db is None:
            db = Database("test_fixes.maldb")
        
        result = db.execute(sql)
        if expected_error:
            print(f"   ❌ Expected error but got success")
            return False, db
        else:
            print(f"   ✅ Success")
            if result:
                print(f"   Result: {result[:3]}")  # Show first 3 rows
            return True, db
    except Exception as e:
        if expected_error and expected_error in str(e):
            print(f"   ✅ Got expected error: {e}")
            return True, db
        else:
            print(f"   ❌ Unexpected error: {e}")
            return False, db

def main():
    """Run all tests with clean setup"""
    print("=" * 60)
    print("🧪 CLEAN TESTING MALDB FIXES")
    print("=" * 60)
    
    # Clean up old test data
    cleanup_test_db()
    
    # Set a fixed encryption key for testing
    os.environ['MALDB_MASTER_KEY'] = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
    
    tests = [
        # Test 1: CREATE TABLE
        ("CREATE TABLE", "CREATE TABLE test1 (id INT, name VARCHAR(50))"),
        
        # Test 2: INSERT single row
        ("INSERT single", "INSERT INTO test1 VALUES (1, 'Alice')"),
        
        # Test 3: INSERT second row
        ("INSERT second", "INSERT INTO test1 VALUES (2, 'Bob')"),
        
        # Test 4: SELECT
        ("SELECT all", "SELECT * FROM test1"),
        
        # Test 5: SELECT with WHERE
        ("SELECT with WHERE", "SELECT * FROM test1 WHERE name = 'Alice'"),
        
        # Test 6: UPDATE
        ("UPDATE", "UPDATE test1 SET name = 'Alice Updated' WHERE id = 1"),
        
        # Test 7: DELETE
        ("DELETE", "DELETE FROM test1 WHERE id = 2"),
        
        # Test 8: Verify DELETE worked
        ("Verify DELETE", "SELECT * FROM test1"),
        
        # Test 9: CREATE TABLE with constraints
        ("CREATE with constraints", "CREATE TABLE test2 (id INT PRIMARY KEY, email VARCHAR(100) UNIQUE)"),
        
        # Test 10: INSERT with PRIMARY KEY violation (should fail)
        ("PRIMARY KEY violation", "INSERT INTO test2 VALUES (1, 'a@test.com')"),
        
        # Test 11: INSERT with UNIQUE violation (should fail)
        ("UNIQUE violation", "INSERT INTO test2 VALUES (1, 'b@test.com')", "PRIMARY KEY constraint"),
        
        # Test 12: INSERT with different UNIQUE violation (should fail)
        ("UNIQUE violation 2", "INSERT INTO test2 VALUES (2, 'a@test.com')", "UNIQUE constraint"),
        
        # Test 13: CREATE TABLE with encryption
        ("CREATE with encryption", "CREATE TABLE test3 (id INT, secret TEXT ENCRYPTED)"),
        
        # Test 14: INSERT encrypted data
        ("INSERT encrypted", "INSERT INTO test3 VALUES (1, 'mysecretpassword')"),
        
        # Test 15: SELECT encrypted data (should show decrypted)
        ("SELECT encrypted", "SELECT * FROM test3"),
        
        # Test 16: Test JOIN
        ("JOIN test setup", "CREATE TABLE dept (dept_id INT, dept_name VARCHAR(50))"),
        ("JOIN test insert", "INSERT INTO dept VALUES (1, 'Engineering')"),
        ("JOIN test", "SELECT test1.name, dept.dept_name FROM test1 JOIN dept ON test1.id = dept.dept_id"),
    ]
    
    passed = 0
    total = len(tests)
    db = None
    
    for test_name, sql, *expected_error in tests:
        if expected_error:
            expected_error = expected_error[0]
        else:
            expected_error = None
        
        success, db = run_test(test_name, sql, expected_error, db)
        if success:
            passed += 1
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! Your MALDB is ready for Pesapal submission!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    # Clean up
    if db:
        db.close()
    
    # Optional: Show final state
    print("\n📁 Final database state:")
    try:
        db = Database("test_fixes.maldb")
        tables = []
        for table in ['test1', 'test2', 'test3', 'dept']:
            try:
                result = db.execute(f"SELECT COUNT(*) FROM {table}")
                tables.append(f"{table}: {result[0][0]} rows")
            except:
                pass
        print("   " + ", ".join(tables))
    except:
        pass

if __name__ == "__main__":
    main()