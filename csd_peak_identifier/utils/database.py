import sqlite3
import os
from datetime import datetime
from csd_peak_identifier.gui.constants import DB_PATH
from .remote_db import RemoteDatabaseBackend

class DatabaseManager:
    """
    Manages database operations with automatic remote/local dispatch.
    Always tries remote first if enabled, falls back to local SQLite.
    """
    
    def __init__(self, db_path=DB_PATH, use_remote=False):
        self.db_path = db_path
        self.remote = RemoteDatabaseBackend()
        self.use_remote = use_remote
        self.is_connected_to_remote = False
        self._initialize_db()
        self.check_connection()

    def check_connection(self):
        """Checks if the remote server is reachable."""
        if not self.use_remote:
            self.is_connected_to_remote = False
            return False
            
        # A simple check: try to get users
        users = self.remote.get_all_users()
        self.is_connected_to_remote = (users is not None)
        return self.is_connected_to_remote

    def toggle_remote(self, use_remote: bool):
        """Toggles remote mode and updates connection status."""
        self.use_remote = use_remote
        return self.check_connection()

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
        if self.use_remote:
            users = self.remote.get_all_users()
            if users is not None:
                self.is_connected_to_remote = True
                return users
            self.is_connected_to_remote = False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users ORDER BY last_used DESC, username ASC")
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        return users

    def add_user(self, username):
        """Adds a new user to the database."""
        if self.use_remote:
            result = self.remote.add_user(username)
            if result is not None:
                self.is_connected_to_remote = True
                return result
            self.is_connected_to_remote = False

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
        if self.use_remote:
            result = self.remote.update_last_used(username)
            if result is not None:
                self.is_connected_to_remote = True
                return result
            self.is_connected_to_remote = False

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
        if self.use_remote:
            stats = self.remote.get_user_stats(username)
            if stats != (0, 0) or self.remote._get("users") is not None:
                self.is_connected_to_remote = True
                return stats
            self.is_connected_to_remote = False

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
        if self.use_remote:
            ts = self.remote.get_random_pending_timestamp(username)
            if ts is not None or self.remote._get("users") is not None:
                self.is_connected_to_remote = True
                return ts
            self.is_connected_to_remote = False

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

    def get_leaderboard(self):
        """Returns the top 3 evaluators [(username, count), ...]"""
        if self.use_remote:
            lb = self.remote.get_leaderboard()
            if lb is not None or self.remote._get("users") is not None:
                self.is_connected_to_remote = True
                return lb
            self.is_connected_to_remote = False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.username, COUNT(DISTINCT e.csd_timestamp) as count
            FROM users u
            JOIN evaluations e ON u.id = e.operator_id
            GROUP BY u.username
            ORDER BY count DESC
            LIMIT 3
        """)
        lb = cursor.fetchall()
        conn.close()
        return lb

    def save_evaluation(self, username, csd_timestamp, isotopes):
        """
        Saves an evaluation to the database.
        isotopes: list of tuples (symbol, s, m, z, status)
        """
        if self.use_remote:
            result = self.remote.save_evaluation(username, csd_timestamp, isotopes)
            if result is not None:
                self.is_connected_to_remote = True
                return result
            self.is_connected_to_remote = False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # Get user ID
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            user_row = cursor.fetchone()
            if not user_row:
                return False
            user_id = user_row[0]

            # Overwrite logic: Remove existing evaluation for this user/CSD if it exists
            cursor.execute(
                "SELECT id FROM evaluations WHERE operator_id = ? AND csd_timestamp = ?",
                (user_id, csd_timestamp)
            )
            old_eval = cursor.fetchone()
            if old_eval:
                old_eval_id = old_eval[0]
                cursor.execute("DELETE FROM evaluation_isotopes WHERE evaluation_id = ?", (old_eval_id,))
                cursor.execute("DELETE FROM evaluations WHERE id = ?", (old_eval_id,))

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

    def get_all_evaluations_for_csd(self, csd_timestamp):
        """
        Returns all evaluations for a specific CSD.
        Returns a list of dicts: [{'operator': username, 'isotopes': [(symbol, status, s, m, z), ...]}]
        """
        if self.use_remote:
            evals = self.remote.get_all_evaluations_for_csd(csd_timestamp)
            if evals is not None or self.remote._get("users") is not None:
                self.is_connected_to_remote = True
                return evals or []
            self.is_connected_to_remote = False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT e.id, u.username
                FROM evaluations e
                JOIN users u ON e.operator_id = u.id
                WHERE e.csd_timestamp = ?
            """, (csd_timestamp,))
            eval_rows = cursor.fetchall()

            results = []
            for eval_id, username in eval_rows:
                cursor.execute("""
                    SELECT symbol, status, s, m, z
                    FROM evaluation_isotopes
                    WHERE evaluation_id = ?
                """, (eval_id,))
                isotopes = cursor.fetchall()
                results.append({
                    'operator': username,
                    'isotopes': isotopes
                })
            return results
        finally:
            conn.close()

    def get_evaluations_summary(self):
        """
        Returns a list of all CSDs in the database with at least one evaluation.
        Returns a list of dicts: [{'csd_timestamp': ts, 'eval_count': count}]
        """
        if self.use_remote:
            summary = self.remote.get_evaluations_summary()
            if summary is not None or self.remote._get("users") is not None:
                self.is_connected_to_remote = True
                return summary or []
            self.is_connected_to_remote = False

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT csd_timestamp, COUNT(id) as eval_count
                FROM evaluations
                GROUP BY csd_timestamp
                HAVING eval_count >= 1
                ORDER BY csd_timestamp DESC
            """)
            rows = cursor.fetchall()
            return [{'csd_timestamp': row[0], 'eval_count': row[1]} for row in rows]
        finally:
            conn.close()
