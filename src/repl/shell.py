"""
Simple SQL REPL (Read-Eval-Print Loop)
"""
import sys
import readline  # For better input handling
from ..core.database import Database

def start_repl(db_file: str = "default.maldb"):
    """Start interactive SQL shell"""
    
    print("=" * 50)
    print("MALDB - Minimal RDBMS")
    print("Type SQL commands (end with ;) or 'exit;' to quit")
    print("=" * 50)
    
    # Initialize database
    try:
        db = Database(db_file)
        print(f"Connected to database: {db_file}")
    except Exception as e:
        print(f"Error initializing database: {e}")
        return
    
    # REPL loop
    while True:
        try:
            # Get input
            line = input("\nmaldb> ").strip()
            
            if not line:
                continue
            
            # Check for exit command
            if line.lower() in ('exit;', 'quit;', 'exit', 'quit'):
                print("Goodbye!")
                break
            
            # Check for help
            if line.lower() in ('help;', 'help'):
                print("\nAvailable commands:")
                print("  CREATE TABLE name (col1 TYPE, col2 TYPE, ...)")
                print("  INSERT INTO table VALUES (val1, val2, ...)")
                print("  SELECT * FROM table")
                print("  exit; - Exit the program")
                continue
            
            # Execute SQL
            try:
                result = db.execute(line)
                # Result is already printed by executor
            except Exception as e:
                print(f"Error: {e}")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Type 'exit;' to quit.")
        except EOFError:
            print("\nGoodbye!")
            break
    
    db.close()

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else "default.maldb"
    start_repl(db_file)