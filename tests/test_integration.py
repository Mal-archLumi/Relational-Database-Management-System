"""
Integration tests
"""
import tempfile
import os
from src.core.database import Database

def test_full_workflow():
    """Test complete database workflow"""
    with tempfile.NamedTemporaryFile(suffix='.maldb', delete=False) as tmp:
        db_file = tmp.name
    
    try:
        # Create database
        db = Database(db_file)
        
        # Create table
        db.execute("CREATE TABLE test (id INT, name VARCHAR(255), value TEXT ENCRYPTED)")
        
        # Insert data
        db.execute("INSERT INTO test VALUES (1, 'Alice', 'secret1')")
        db.execute("INSERT INTO test VALUES (2, 'Bob', 'secret2')")
        
        # Query data
        result = db.execute("SELECT id, name FROM test")
        assert len(result) == 2
        assert (1, 'Alice') in result
        assert (2, 'Bob') in result
        
        # Query with column selection
        result = db.execute("SELECT name FROM test")
        assert len(result) == 2
        assert ('Alice',) in result
        assert ('Bob',) in result
        
        # Drop table
        db.execute("DROP TABLE test")
        
        # Verify table is gone
        try:
            db.execute("SELECT * FROM test")
            assert False, "Should have raised error"
        except:
            pass
            
    finally:
        # Cleanup
        if os.path.exists(db_file):
            os.remove(db_file)
        data_dir = db_file.replace('.maldb', '_data')
        if os.path.exists(data_dir):
            import shutil
            shutil.rmtree(data_dir)