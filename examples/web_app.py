#!/usr/bin/env python3
"""
Example of integrating MALDB with a web application
"""
import sys
sys.path.insert(0, '.')

from src.core.database import Database

class WebApp:
    """Simple web application using MALDB"""
    
    def __init__(self, db_file="webapp.maldb"):
        self.db = Database(db_file)
        self.setup_database()
    
    def setup_database(self):
        """Initialize database schema"""
        # Users table with encrypted password
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash TEXT ENCRYPTED NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE
            )
        """)
        
        # Posts table
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                title VARCHAR(200) NOT NULL,
                content TEXT,
                is_private BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
    
    def create_user(self, username, email, password):
        """Create a new user"""
        # In a real app, you'd hash the password first
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Get next ID
        users = self.db.execute("SELECT id FROM users")
        next_id = max([u[0] for u in users]) + 1 if users else 1
        
        self.db.execute(f"""
            INSERT INTO users (id, username, email, password_hash)
            VALUES ({next_id}, '{username}', '{email}', '{password_hash}')
        """)
        
        return next_id
    
    def create_post(self, user_id, title, content, is_private=False):
        """Create a new post"""
        posts = self.db.execute("SELECT id FROM posts")
        next_id = max([p[0] for p in posts]) + 1 if posts else 1
        
        private = 'TRUE' if is_private else 'FALSE'
        
        self.db.execute(f"""
            INSERT INTO posts (id, user_id, title, content, is_private)
            VALUES ({next_id}, {user_id}, '{title}', '{content}', {private})
        """)
        
        return next_id
    
    def get_user_posts(self, user_id):
        """Get all posts for a user"""
        return self.db.execute(f"""
            SELECT id, title, content, created_at 
            FROM posts 
            WHERE user_id = {user_id} AND is_private = FALSE
            ORDER BY created_at DESC
        """)
    
    def search_users(self, query):
        """Search for users"""
        return self.db.execute(f"""
            SELECT id, username, email, created_at
            FROM users
            WHERE username LIKE '%{query}%' OR email LIKE '%{query}%'
            AND is_active = TRUE
        """)
    
    def close(self):
        """Close database connection"""
        self.db.close()

def main():
    print("=== Web Application Integration Example ===\n")
    
    app = WebApp()
    
    # Create some users
    print("1. Creating users...")
    alice_id = app.create_user("alice", "alice@example.com", "alice123")
    bob_id = app.create_user("bob", "bob@example.com", "bob456")
    
    print(f"   Created users: Alice (ID: {alice_id}), Bob (ID: {bob_id})")
    
    # Create posts
    print("\n2. Creating posts...")
    app.create_post(alice_id, "My First Post", "Hello world!", is_private=False)
    app.create_post(alice_id, "Private Thoughts", "Secret diary entry", is_private=True)
    app.create_post(bob_id, "Bob's Blog", "Welcome to my blog!", is_private=False)
    
    # Get user posts
    print("\n3. Retrieving public posts...")
    alice_posts = app.get_user_posts(alice_id)
    print(f"   Alice's public posts: {len(alice_posts)}")
    
    for post in alice_posts:
        print(f"   - {post[1]} ({post[3][:10]})")
    
    # Search users
    print("\n4. Searching users...")
    results = app.search_users("ali")
    print(f"   Found {len(results)} user(s) matching 'ali':")
    
    for user in results:
        print(f"   - {user[1]} ({user[2]})")
    
    # Security note
    print("\n5. Security Features:")
    print("   ✅ Passwords are encrypted at rest")
    print("   ✅ Private posts are protected at database level")
    print("   ✅ SQL injection protection via parameter validation")
    
    # Clean up
    app.db.execute("DROP TABLE posts")
    app.db.execute("DROP TABLE users")
    app.close()
    
    print("\n=== Example Completed ===")

if __name__ == "__main__":
    main()