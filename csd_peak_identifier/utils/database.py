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

        # Table for evaluations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                csd_timestamp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES users (id)
            )
        ''')

        # Table for identified isotopes within an evaluation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluation_isotopes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                evaluation_id INTEGER,
                symbol TEXT NOT NULL,
                s TEXT,
                m INTEGER,
                z INTEGER,
                status TEXT NOT NULL, -- 'identified' or 'maybe'
                FOREIGN KEY (evaluation_id) REFERENCES evaluations (id)
            )
        ''')
        
        # Migration: Add columns if they don't exist (for existing databases)
        cursor.execute("PRAGMA table_info(evaluation_isotopes)")
        columns = [column[1] for column in cursor.fetchall()]
        if "s" not in columns:
            cursor.execute("ALTER TABLE evaluation_isotopes ADD COLUMN s TEXT")
        if "m" not in columns:
            cursor.execute("ALTER TABLE evaluation_isotopes ADD COLUMN m INTEGER")
        if "z" not in columns:
            cursor.execute("ALTER TABLE evaluation_isotopes ADD COLUMN z INTEGER")
        
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

    def get_user_stats(self, username):
        """
        Returns (eval_count, pending_count)
        eval_count: Unique CSDs evaluated by this user
        pending_count: Unique CSDs evaluated by others but NOT by this user
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                # New user: eval_count is 0, pending is total unique CSDs in DB
                cursor.execute("SELECT COUNT(DISTINCT csd_timestamp) FROM evaluations")
                return 0, cursor.fetchone()[0]
            user_id = user_row[0]

            # Count user's evaluations
            cursor.execute(
                "SELECT COUNT(DISTINCT csd_timestamp) FROM evaluations WHERE operator_id = ?",
                (user_id,)
            )
            eval_count = cursor.fetchone()[0]

            # Count pending (by others, not by me)
            cursor.execute("""
                SELECT COUNT(DISTINCT csd_timestamp) FROM evaluations 
                WHERE operator_id != ? 
                AND csd_timestamp NOT IN (SELECT csd_timestamp FROM evaluations WHERE operator_id = ?)
            """, (user_id, user_id))
            pending_count = cursor.fetchone()[0]

            return eval_count, pending_count
        finally:
            conn.close()

    def get_random_pending_timestamp(self, username):
        """Returns a random csd_timestamp evaluated by others but not this user."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                # New user: pick any random unique CSD from evaluations
                cursor.execute("SELECT DISTINCT csd_timestamp FROM evaluations ORDER BY RANDOM() LIMIT 1")
                row = cursor.fetchone()
                return row[0] if row else None
            user_id = user_row[0]

            cursor.execute("""
                SELECT DISTINCT csd_timestamp FROM evaluations 
                WHERE operator_id != ? 
                AND csd_timestamp NOT IN (SELECT csd_timestamp FROM evaluations WHERE operator_id = ?)
                ORDER BY RANDOM() LIMIT 1
            """, (user_id, user_id))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def save_evaluation(self, username, csd_timestamp, isotopes):
        """
        Saves an evaluation to the database.
        isotopes: list of tuples (symbol, s, m, z, status)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            user_id = user_row[0]

            # Insert evaluation
            cursor.execute(
                "INSERT INTO evaluations (operator_id, csd_timestamp) VALUES (?, ?)",
                (user_id, csd_timestamp)
            )
            eval_id = cursor.lastrowid

            # Insert isotopes
            for iso in isotopes:
                # Ensure we handle both old 2-tuple and new 5-tuple formats during transition
                if len(iso) == 5:
                    symbol, s, m, z, status = iso
                else:
                    symbol, status = iso
                    s, m, z = None, None, None

                cursor.execute(
                    "INSERT INTO evaluation_isotopes (evaluation_id, symbol, s, m, z, status) VALUES (?, ?, ?, ?, ?, ?)",
                    (eval_id, symbol, s, m, z, status)
                )

            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database error saving evaluation: {e}")
            return False
        finally:
            conn.close()
