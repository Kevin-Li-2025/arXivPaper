import sqlite3
import logging
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from config import Config

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = Config.DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE NOT NULL,
                    name TEXT,
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_notified TIMESTAMP
                )
            """)
            
            # Papers table to track sent papers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    summary TEXT,
                    published TIMESTAMP,
                    score REAL DEFAULT 0,
                    url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Sent notifications table to avoid duplicates
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sent_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    paper_id TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (paper_id) REFERENCES papers (id),
                    UNIQUE(user_id, paper_id)
                )
            """)
            
            conn.commit()
    
    def add_user(self, email: str, name: str = None) -> Optional[int]:
        """Add a new user to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (email, name) VALUES (?, ?)",
                    (email, name)
                )
                conn.commit()
                user_id = cursor.lastrowid
                logger.info(f"Added new user: {email} with ID {user_id}")
                return user_id
        except sqlite3.IntegrityError:
            logger.warning(f"User already exists: {email}")
            return None
        except Exception as e:
            logger.error(f"Error adding user {email}: {e}")
            return None
    
    def get_active_users(self) -> List[Tuple[int, str, str]]:
        """Get all active users."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name FROM users WHERE active = 1"
            )
            return cursor.fetchall()
    
    def get_all_users(self) -> List[Tuple]:
        """Get all users (active and inactive)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, email, name, last_notified FROM users ORDER BY id"
            )
            return cursor.fetchall()
    
    def remove_user(self, user_id: int) -> bool:
        """Remove a user from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # First remove sent notifications
                cursor.execute("DELETE FROM sent_notifications WHERE user_id = ?", (user_id,))
                # Then remove user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                logger.info(f"Removed user with ID {user_id}")
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error removing user {user_id}: {e}")
            return False
    
    def deactivate_user(self, email: str) -> bool:
        """Deactivate a user (unsubscribe)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET active = 0 WHERE email = ?",
                    (email,)
                )
                conn.commit()
                logger.info(f"Deactivated user: {email}")
                return True
        except Exception as e:
            logger.error(f"Error deactivating user {email}: {e}")
            return False
    
    def add_paper(self, paper) -> bool:
        """Add a paper to the database. Accepts both dict and separate parameters."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if isinstance(paper, dict):
                    # Handle dict format
                    paper_id = paper.get('id', '')
                    title = paper.get('title', '')
                    authors = paper.get('authors', '')
                    summary = paper.get('summary', '')
                    published = paper.get('published')
                    score = paper.get('score', 0.0)
                    url = paper.get('url', '')
                else:
                    # Handle tuple/list format (backward compatibility)
                    paper_id, title, authors, summary, published, score, url = paper
                
                # Check if paper already exists
                cursor.execute("SELECT id FROM papers WHERE id = ?", (paper_id,))
                if cursor.fetchone():
                    return False  # Paper already exists
                
                cursor.execute("""
                    INSERT INTO papers 
                    (id, title, authors, summary, published, score, url)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (paper_id, title, authors, summary, published, score, url))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding paper: {e}")
            return False
    
    def get_top_papers(self, limit: int = 20, min_score: float = None) -> List[Dict]:
        """Get top papers by score."""
        if min_score is None:
            min_score = 0  # Get all papers by default
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, authors, summary, url, published, score
                FROM papers
                WHERE score >= ?
                ORDER BY score DESC, published DESC
                LIMIT ?
            """, (min_score, limit))
            
            columns = ['id', 'title', 'authors', 'summary', 'url', 'published', 'score']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def clear_papers(self):
        """Clear all papers from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sent_notifications")
                cursor.execute("DELETE FROM papers")
                conn.commit()
                logger.info("Cleared all papers from database")
        except Exception as e:
            logger.error(f"Error clearing papers: {e}")
    
    def reset_all_notification_timestamps(self):
        """Reset notification timestamps for all users."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET last_notified = NULL")
                conn.commit()
                logger.info("Reset all user notification timestamps")
        except Exception as e:
            logger.error(f"Error resetting notification timestamps: {e}")
    
    def update_user_last_notification(self, user_id: int):
        """Update the last notification timestamp for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET last_notified = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating last notification for user {user_id}: {e}")
    
    def get_papers_not_sent_to_user(self, user_id: int, min_score: float = Config.MIN_SCORE_THRESHOLD) -> List[dict]:
        """Get papers that haven't been sent to a specific user."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.title, p.authors, p.summary, p.published, p.score, p.url
                FROM papers p
                WHERE p.score >= ? 
                AND p.id NOT IN (
                    SELECT sn.paper_id 
                    FROM sent_notifications sn 
                    WHERE sn.user_id = ?
                )
                ORDER BY p.score DESC, p.published DESC
            """, (min_score, user_id))
            
            columns = ['id', 'title', 'authors', 'summary', 'published', 'score', 'url']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def mark_paper_sent(self, user_id: int, paper_id: str):
        """Mark a paper as sent to a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR IGNORE INTO sent_notifications (user_id, paper_id) VALUES (?, ?)",
                    (user_id, paper_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error marking paper {paper_id} as sent to user {user_id}: {e}")
    
    def update_user_last_notified(self, user_id: int):
        """Update the last notification timestamp for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET last_notified = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating last notified for user {user_id}: {e}")
    
    def reset_user_notifications(self, user_id: int):
        """Reset a user's notification history so they can receive all papers again."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM sent_notifications WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                logger.info(f"Reset notification history for user {user_id}")
        except Exception as e:
            logger.error(f"Error resetting notifications for user {user_id}: {e}")
    
    def reset_user_notifications_by_email(self, email: str):
        """Reset a user's notification history by email."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id FROM users WHERE email = ?",
                    (email,)
                )
                result = cursor.fetchone()
                if result:
                    user_id = result[0]
                    self.reset_user_notifications(user_id)
                    return True
                else:
                    logger.warning(f"User not found: {email}")
                    return False
        except Exception as e:
            logger.error(f"Error resetting notifications for user {email}: {e}")
            return False
    
    def get_all_papers_for_user(self, user_id: int, min_score: float = None) -> List[dict]:
        """Get ALL papers for a user, regardless of whether they've been sent before."""
        if min_score is None:
            min_score = Config.MIN_SCORE_THRESHOLD
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, authors, summary, published, score, url
                FROM papers
                WHERE score >= ?
                ORDER BY score DESC, published DESC
            """, (min_score,))
            
            columns = ['id', 'title', 'authors', 'summary', 'published', 'score', 'url']
            return [dict(zip(columns, row)) for row in cursor.fetchall()] 