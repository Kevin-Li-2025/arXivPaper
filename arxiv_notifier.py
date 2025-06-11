import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import DatabaseManager
from arxiv_client import ArxivClient
from paper_scorer import PaperScorer
from email_notifier import EmailNotifier
from config import Config

logger = logging.getLogger(__name__)

class ArxivNotifier:
    def __init__(self, scoring_method: str = None):
        self.db = DatabaseManager()
        self.arxiv_client = ArxivClient()
        self.scorer = PaperScorer(scoring_method)
        self.email_notifier = EmailNotifier()
        
        # Log the scoring method being used
        method_info = self.scorer.get_method_info()
        logger.info(f"ArxivNotifier initialized with {method_info['name']}")
    
    def run_notifications(self, force: bool = False) -> Dict:
        """Run the complete notification pipeline."""
        try:
            logger.info("Starting notification pipeline...")
            
            # Step 1: Fetch and score new papers
            new_papers = self._fetch_and_score_papers()
            
            # Step 2: Get users who need notifications
            users = self._get_users_for_notification(force)
            
            if not users:
                logger.info("No users need notifications at this time")
                return {
                    'success': True,
                    'emails_sent': 0,
                    'papers_sent': 0,
                    'new_papers': len(new_papers),
                    'message': 'No users need notifications'
                }
            
            # Step 3: Send notifications
            emails_sent = 0
            total_papers_sent = 0
            
            for user in users:
                try:
                    # Get top papers for this user
                    top_papers = self.db.get_top_papers(limit=10)
                    
                    if top_papers:
                        success = self.email_notifier.send_notification(user[1], user[2] or "Researcher", top_papers)
                        if success:
                            emails_sent += 1
                            total_papers_sent += len(top_papers)
                            # Update last notification time
                            self.db.update_user_last_notification(user[0])
                            logger.info(f"Sent {len(top_papers)} papers to {user[1]}")
                        else:
                            logger.error(f"Failed to send email to {user[1]}")
                    
                except Exception as e:
                    logger.error(f"Error sending notification to {user[1]}: {e}")
                    continue
            
            logger.info(f"Notification pipeline complete: {emails_sent} emails sent, {total_papers_sent} papers total")
            
            return {
                'success': True,
                'emails_sent': emails_sent,
                'papers_sent': total_papers_sent,
                'new_papers': len(new_papers),
                'users_processed': len(users)
            }
            
        except Exception as e:
            logger.error(f"Error in notification pipeline: {e}")
            return {
                'success': False,
                'error': str(e),
                'emails_sent': 0,
                'papers_sent': 0,
                'new_papers': 0
            }
    
    def _fetch_and_score_papers(self) -> int:
        """Fetch new papers from arXiv and score them."""
        try:
            logger.info("Fetching papers from arXiv...")
            papers = self.arxiv_client.fetch_recent_papers()
            
            if not papers:
                logger.warning("No papers fetched from arXiv")
                return 0
            
            logger.info(f"Fetched {len(papers)} papers, now scoring...")
            
            # Score the papers
            scored_papers = self.scorer.score_papers(papers)
            
            # Save to database
            new_papers_count = 0
            for paper in scored_papers:
                if self.db.add_paper(paper):
                    new_papers_count += 1
            
            logger.info(f"Added {new_papers_count} new papers to database")
            return new_papers_count
            
        except Exception as e:
            logger.error(f"Error fetching and scoring papers: {e}")
            return 0
    
    def _get_users_for_notification(self, force: bool = False) -> list:
        """Get users who need notifications."""
        users = self.db.get_all_users()
        
        if force:
            logger.info(f"Force mode: sending to all {len(users)} users")
            return users
        
        # Filter users based on last notification time
        users_to_notify = []
        notification_threshold = datetime.now() - timedelta(hours=Config.UPDATE_FREQUENCY)
        
        for user in users:
            last_notification = user[3] if len(user) > 3 and user[3] else None
            
            if last_notification is None:
                # Never notified before
                users_to_notify.append(user)
            elif isinstance(last_notification, str):
                # Parse string timestamp
                try:
                    last_notification_dt = datetime.strptime(last_notification, '%Y-%m-%d %H:%M:%S')
                    if last_notification_dt < notification_threshold:
                        users_to_notify.append(user)
                except ValueError:
                    # Invalid timestamp, add user
                    users_to_notify.append(user)
            elif hasattr(last_notification, 'replace'):
                # DateTime object
                if last_notification.replace(tzinfo=None) < notification_threshold:
                    users_to_notify.append(user)
            else:
                # Unknown format, add user to be safe
                users_to_notify.append(user)
        
        logger.info(f"Found {len(users_to_notify)} users who need notifications")
        return users_to_notify
    
    def switch_scoring_method(self, method: str):
        """Switch to a different scoring method."""
        try:
            self.scorer.switch_method(method)
            method_info = self.scorer.get_method_info()
            logger.info(f"Switched to {method_info['name']}")
        except Exception as e:
            logger.error(f"Failed to switch scoring method: {e}")
            raise
    
    def get_scoring_info(self) -> Dict:
        """Get information about the current scoring method."""
        return self.scorer.get_method_info()
    
    def register_user(self, email: str, name: str = None) -> bool:
        """Register a new user."""
        try:
            user_id = self.db.add_user(email, name)
            if user_id:
                logger.info(f"Registered new user: {email}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to register user {email}: {e}")
            return False
    
    def send_notification_to_user(self, email: str, paper_count: int = 10) -> bool:
        """Send notification to a specific user."""
        try:
            # Get user
            users = self.db.get_all_users()
            user = next((u for u in users if u[1] == email), None)
            
            if not user:
                logger.error(f"User {email} not found")
                return False
            
            # Get top papers
            papers = self.db.get_top_papers(limit=paper_count)
            if not papers:
                logger.warning("No papers available to send")
                return False
            
            # Send notification
            success = self.email_notifier.send_notification(user[1], user[2] or "Researcher", papers)
            
            if success:
                # Update last notification time
                self.db.update_user_last_notification(user[0])
                logger.info(f"Sent {len(papers)} papers to {email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification to {email}: {e}")
            return False
    
    def update_papers(self) -> int:
        """Fetch new papers from arXiv and update the database."""
        logger.info("Starting paper update process...")
        
        # Fetch recent papers
        papers = self.arxiv_client.fetch_recent_papers()
        if not papers:
            logger.warning("No papers fetched from arXiv")
            return 0
        
        # Score papers
        scored_papers = self.scorer.score_papers(papers)
        
        # Store papers in database
        stored_count = 0
        for paper in scored_papers:
            try:
                self.db.add_paper(
                    paper_id=paper['id'],
                    title=paper['title'],
                    authors=paper['authors'],
                    summary=paper['summary'],
                    published=paper['published'],
                    score=paper['score'],
                    url=paper['url']
                )
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing paper {paper['id']}: {e}")
        
        logger.info(f"Updated {stored_count} papers in database")
        return stored_count
    
    def send_notifications(self, force_send: bool = False) -> Dict[str, int]:
        """Send notifications to all active users."""
        logger.info("Starting notification process...")
        
        results = {
            'users_processed': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'papers_sent': 0
        }
        
        # Get all active users
        users = self.db.get_active_users()
        
        for user_id, email, name in users:
            results['users_processed'] += 1
            
            try:
                # Get papers - either new ones only or all papers if force_send
                if force_send:
                    papers = self.db.get_all_papers_for_user(user_id)
                else:
                    papers = self.db.get_papers_not_sent_to_user(user_id)
                
                if papers:
                    # Send notification
                    success = self.email_notifier.send_notification(email, name, papers)
                    
                    if success:
                        # Mark papers as sent (only if not forcing)
                        if not force_send:
                            for paper in papers:
                                self.db.mark_paper_sent(user_id, paper['id'])
                        
                        # Update user's last notification timestamp
                        self.db.update_user_last_notified(user_id)
                        
                        results['emails_sent'] += 1
                        results['papers_sent'] += len(papers)
                        
                        logger.info(f"Sent {len(papers)} papers to {email}")
                    else:
                        results['emails_failed'] += 1
                        logger.error(f"Failed to send notification to {email}")
                else:
                    logger.info(f"No new papers to send to {email}")
                    
            except Exception as e:
                logger.error(f"Error processing user {email}: {e}")
                results['emails_failed'] += 1
        
        logger.info(f"Notification process complete: {results}")
        return results
    
    def reset_user_notifications(self, email: str) -> bool:
        """Reset a user's notification history so they can receive all papers again."""
        return self.db.reset_user_notifications_by_email(email)
    
    def unsubscribe_user(self, email: str) -> bool:
        """Unsubscribe a user from notifications."""
        success = self.db.deactivate_user(email)
        if success:
            logger.info(f"Unsubscribed user: {email}")
        return success
    
    def get_top_papers(self, limit: int = 10, min_score: float = None) -> List[Dict]:
        """Get top-scored papers from the database."""
        if min_score is None:
            min_score = Config.MIN_SCORE_THRESHOLD
        
        # This is a simplified version - you might want to add this method to DatabaseManager
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, authors, summary, published, score, url
                FROM papers
                WHERE score >= ?
                ORDER BY score DESC, published DESC
                LIMIT ?
            """, (min_score, limit))
            
            columns = ['id', 'title', 'authors', 'summary', 'published', 'score', 'url']
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_user_count(self) -> int:
        """Get the number of active users."""
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE active = 1")
            return cursor.fetchone()[0]
    
    def run_full_update(self) -> Dict:
        """Run a complete update cycle: fetch papers and send notifications."""
        logger.info("Starting full update cycle...")
        
        results = {
            'papers_updated': 0,
            'notifications': {},
            'start_time': datetime.now(),
            'end_time': None
        }
        
        try:
            # Update papers
            results['papers_updated'] = self.update_papers()
            
            # Send notifications
            results['notifications'] = self.send_notifications()
            
            results['end_time'] = datetime.now()
            results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
            
            logger.info(f"Full update cycle completed in {results['duration']:.1f} seconds")
            
        except Exception as e:
            logger.error(f"Error during full update cycle: {e}")
            results['error'] = str(e)
        
        return results
    
    def test_email_setup(self) -> bool:
        """Test the email configuration."""
        return self.email_notifier.test_connection() 