"""
Simple SQL REPL that works reliably
"""
import sys
import readline  # For better input handling
from ..core.database import Database

def start_repl(db_file: str = "default.maldb"):
    """Start interactive SQL shell"""
    
    print("=" * 60)
    print("MALDB - Minimal RDBMS with Column-Level Encryption")
    print("Type SQL commands (without comments) or 'exit;' to quit")
    print("Type 'help;' for available commands")
    print("=" * 60)
    
    # Initialize database
    try:
        db = Database(db_file)
        print(f"📁 Connected to database: {db_file}")
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return
    
    # Enable command history
    try:
        readline.read_history_file(".maldb_history")
    except FileNotFoundError:
        pass
    
    # REPL loop
    while True:
        try:
            # Get input
            line = input("\nmaldb> ").strip()
            
            if not line:
                continue
            
            # Add to history
            readline.add_history(line)
            
            # Check for exit command
            if line.lower() in ('exit;', 'quit;', 'exit', 'quit'):
                print("👋 Goodbye!")
                break
            
            # Check for help
            if line.lower() in ('help;', 'help'):
                print("\n📖 MALDB SQL Commands:")
                print("   CREATE TABLE name (col1 TYPE, col2 TYPE, ...)")
                print("   INSERT INTO table VALUES (val1, val2, ...)")
                print("   SELECT * FROM table")
                print("   SELECT col1, col2 FROM table")
                print("   DROP TABLE name")
                print("   help; - Show this help")
                print("   exit; - Exit the program")
                print("\n📋 Supported types: INT, VARCHAR(N), TEXT, BOOLEAN")
                print("📋 Constraints: PRIMARY KEY, UNIQUE, NOT NULL, ENCRYPTED")
                print("\n💡 Examples:")
                print("   CREATE TABLE users (id INT, name VARCHAR(255))")
                print("   INSERT INTO users VALUES (1, 'Alice')")
                print("   SELECT * FROM users")
                continue
            
            # Check for multiple commands in one line
            if line.count(';') > 1:
                print("❌ Error: Please enter only one SQL command per line")
                print("💡 Tip: Type commands separately:")
                print("      DROP TABLE users;")
                print("      Then: CREATE TABLE employees (...);")
                continue
            
            # Execute SQL
            try:
                result = db.execute(line)
                # Result is already printed by executor
            except Exception as e:
                print(f"❌ Error: {e}")
        
        except KeyboardInterrupt:
            print("\n\n💡 Type 'exit;' to quit or continue with commands.")
        except EOFError:
            print("\n👋 Goodbye!")
            break
    
    # Save history
    try:
        readline.write_history_file(".maldb_history")
    except:
        pass
    
    db.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "default.maldb"
    start_repl(db_file)