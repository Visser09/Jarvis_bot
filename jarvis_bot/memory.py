import sqlite3
from datetime import datetime

class Memory:
    def __init__(self, db_path="memory.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Create tables for storing conversation history and user preferences."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                user_input TEXT,
                ai_response TEXT
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        self.conn.commit()

    def store_conversation(self, user_input, ai_response):
        """Store conversation in the database."""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            "INSERT INTO conversations (timestamp, user_input, ai_response) VALUES (?, ?, ?)",
            (timestamp, user_input, ai_response)
        )
        self.conn.commit()

    def get_recent_conversations(self, limit=5):
        """Retrieve the last few interactions."""
        self.cursor.execute("SELECT user_input, ai_response FROM conversations ORDER BY id DESC LIMIT ?", (limit,))
        return self.cursor.fetchall()

    def store_user_data(self, key, value):
        """Store persistent user data (e.g., name, preferences)."""
        self.cursor.execute("REPLACE INTO user_data (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_user_data(self, key):
        """Retrieve stored user data."""
        self.cursor.execute("SELECT value FROM user_data WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def clear_memory(self):
        """Wipe stored conversations and user data."""
        self.cursor.execute("DELETE FROM conversations")
        self.cursor.execute("DELETE FROM user_data")
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

# Example Usage
if __name__ == "__main__":
    memory = Memory()
    memory.store_conversation("Hello, what's my name?", "Your name is Mitchel!")
    print(memory.get_recent_conversations())
    memory.store_user_data("name", "Mitchel")
    print(memory.get_user_data("name"))
