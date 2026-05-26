import sqlite3
import os
from datetime import datetime
from ..gui.constants import DB_PATH

class DatabaseManager:
    """Manages local SQLite database for user profiles."""
    
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Creates the database and necessary tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for user profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()

    def get_all_users(self):
        """Returns a list of all usernames, sorted by last used date."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users ORDER BY last_used DESC, username ASC")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def add_user(self, username):
        """Adds a new user to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    def update_last_used(self, username):
        """Updates the last_used timestamp for a specific user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET last_used = ? WHERE username = ?",
            (datetime.now().isoformat(), username)
        )
        conn.commit()
        conn.close()

    def delete_user(self, username):
        """Deletes a user from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
