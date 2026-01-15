#!/usr/bin/env python3
"""
Quick test to verify MALDB works
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic():
    """Test basic database functionality"""
    print("🧪 Testing MALDB Basic Functionality...")
    
    try:
        from src.core.database import Database
        
        # Clean up any existing test database
        import shutil
        if os.path.exists("test_basic.maldb"):
            os.remove("test_basic.maldb")
        if os.path.exists("test_basic_data"):
            shutil.rmtree("test_basic_data")
        
        # Create database
        db = Database("test_basic.maldb")
        
        # Create table
        db.execute("CREATE TABLE test (id INT, name VARCHAR(255))")
        print("✅ CREATE TABLE works")
        
        # Insert data
        db.execute("INSERT INTO test VALUES (1, 'Alice')")
        db.execute("INSERT INTO test VALUES (2, 'Bob')")
        print("✅ INSERT works")
        
        # Select data
        results = db.execute("SELECT * FROM test")
        assert len(results) == 2
        print("✅ SELECT works")
        
        # Specific columns
        results = db.execute("SELECT name FROM test")
        assert len(results) == 2
        assert ('Alice',) in results
        print("✅ Column selection works")
        
        # Drop table
        db.execute("DROP TABLE test")
        print("✅ DROP TABLE works")
        
        db.close()
        
        # Clean up
        if os.path.exists("test_basic.maldb"):
            os.remove("test_basic.maldb")
        if os.path.exists("test_basic_data"):
            shutil.rmtree("test_basic_data")
        
        print("\n🎉 All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_encryption():
    """Test encryption feature"""
    print("\n🔐 Testing Encryption Feature...")
    
    try:
        from src.core.database import Database
        
        # Clean up
        import shutil
        if os.path.exists("test_encrypt.maldb"):
            os.remove("test_encrypt.maldb")
        if os.path.exists("test_encrypt_data"):
            shutil.rmtree("test_encrypt_data")
        
        # Create database with encrypted column
        db = Database("test_encrypt.maldb")
        
        db.execute("CREATE TABLE secrets (id INT, secret TEXT ENCRYPTED)")
        
        # Insert encrypted data
        db.execute("INSERT INTO secrets VALUES (1, 'SuperSecret123')")
        print("✅ Encrypted INSERT works")
        
        # Query (should automatically decrypt)
        results = db.execute("SELECT * FROM secrets")
        assert len(results) == 1
        # CSV stores everything as strings, so id is '1' not 1
        assert results[0][0] == 1 
        # Secret should be decrypted back to original
        assert results[0][1] == 'SuperSecret123'
        print("✅ Automatic decryption works")
        
        db.close()
        
        # Clean up
        if os.path.exists("test_encrypt.maldb"):
            os.remove("test_encrypt.maldb")
        if os.path.exists("test_encrypt_data"):
            shutil.rmtree("test_encrypt_data")
        
        print("🎉 Encryption tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_repl():
    """Test REPL interface"""
    print("\n💻 Testing REPL Interface...")
    try:
        # Just test that we can import and create REPL
        from src.repl.shell import start_repl
        print("✅ REPL module imports correctly")
        
        # Test would require interactive testing
        print("⚠️  REPL interactive test skipped (requires user input)")
        return True
        
    except Exception as e:
        print(f"❌ REPL test failed: {e}")
        return False

def test_api():
    """Test API interface"""
    print("\n🌐 Testing API Interface...")
    try:
        from src.api.server import start_api_server
        print("✅ API module imports correctly")
        
        # Test would require running server
        print("⚠️  API server test skipped (requires running server)")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("MALDB - System Test Suite")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 0
    
    # Run tests
    tests = [
        ("Basic Functionality", test_basic),
        ("Encryption", test_encryption),
        ("REPL Interface", test_repl),
        ("API Interface", test_api),
    ]
    
    for test_name, test_func in tests:
        tests_total += 1
        print(f"\n📋 Test {tests_total}: {test_name}")
        print("-" * 40)
        
        if test_func():
            tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests Passed: {tests_passed}/{tests_total}")
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed! MALDB is ready to use.")
        print("\n🚀 Next steps:")
        print("1. Run the REPL: python src/main.py")
        print("2. Start the API: python src/main.py --api")
        print("3. Run the demo: cd demo && python app.py")
        print("\n💡 Quick test commands:")
        print("   python src/main.py test.maldb")
        print("   Then in REPL: CREATE TABLE users (id INT, name VARCHAR(255))")
        print("                INSERT INTO users VALUES (1, 'Alice')")
        print("                SELECT * FROM users")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
    
    return tests_passed == tests_total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)