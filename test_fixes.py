#!/usr/bin/env python3
"""
Test all fixes for MALDB
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import Database

def run_test(test_name, sql, expected_error=None):
    """Run a single test"""
    print(f"\n🧪 {test_name}")
    print(f"   SQL: {sql}")
    
    try:
        db = Database("test_fixes.maldb")
        result = db.execute(sql)
        if expected_error:
            print(f"   ❌ Expected error but got success")
            return False
        else:
            print(f"   ✅ Success")
            if result:
                print(f"   Result: {result}")
            return True
    except Exception as e:
        if expected_error and expected_error in str(e):
            print(f"   ✅ Got expected error: {e}")
            return True
        else:
            print(f"   ❌ Unexpected error: {e}")
            return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 TESTING MALDB FIXES")
    print("=" * 60)
    
    tests = [
        # Test 1: CREATE TABLE
        ("CREATE TABLE", "CREATE TABLE test1 (id INT, name VARCHAR(50))"),
        
        # Test 2: INSERT single row
        ("INSERT single", "INSERT INTO test1 VALUES (1, 'Alice')"),
        
        # Test 3: INSERT multiple rows (should work one at a time)
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
        ("PRIMARY KEY violation", "INSERT INTO test2 VALUES (1, 'a@test.com')", "PRIMARY KEY constraint"),
        
        # Test 11: INSERT with UNIQUE violation (should fail)
        ("UNIQUE violation", "INSERT INTO test2 VALUES (2, 'a@test.com')", "UNIQUE constraint"),
        
        # Test 12: CREATE TABLE with encryption
        ("CREATE with encryption", "CREATE TABLE test3 (id INT, secret TEXT ENCRYPTED)"),
        
        # Test 13: INSERT encrypted data
        ("INSERT encrypted", "INSERT INTO test3 VALUES (1, 'mysecretpassword')"),
        
        # Test 14: SELECT encrypted data
        ("SELECT encrypted", "SELECT * FROM test3"),
        
        # Test 15: Multiple INSERTs in one command (should fail gracefully)
        ("Multiple INSERTs", "INSERT INTO test1 VALUES (3, 'Carol'); INSERT INTO test1 VALUES (4, 'Dave')", None),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, sql, *expected_error in tests:
        if expected_error:
            expected_error = expected_error[0]
        else:
            expected_error = None
        
        if run_test(test_name, sql, expected_error):
            passed += 1
    
    print(f"\n" + "=" * 60)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("🎉 All tests passed! Your MALDB is ready for Pesapal submission!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    # Clean up test database
    try:
        import shutil
        if os.path.exists("test_fixes.maldb_data"):
            shutil.rmtree("test_fixes.maldb_data")
    except:
        pass

if __name__ == "__main__":
    main()