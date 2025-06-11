#!/usr/bin/env python3
"""
CLI interface for the arXiv paper notifier system.
"""

import click
import logging
import schedule
import time
from datetime import datetime
from arxiv_notifier import ArxivNotifier
from config import Config
from database import DatabaseManager
from arxiv_client import ArxivClient
from paper_scorer import PaperScorer
from email_notifier import EmailNotifier
from scorer_factory import ScorerFactory
from dateutil import parser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arxiv_notifier.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """arXiv Paper Notifier - Stay updated with top CS.AI papers."""
    pass

@cli.command()
@click.option('--email', required=True, help='Email address to register')
@click.option('--name', help='Name of the user (optional)')
def register(email, name):
    """Register a new user for paper notifications."""
    try:
        db = DatabaseManager()
        user_id = db.add_user(email, name)
        if user_id:
            click.echo(f"✅ User registered successfully with ID: {user_id}")
            click.echo(f"📧 {email} will now receive top CS.AI paper notifications")
        else:
            click.echo("❌ Registration failed - user might already exist")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def users():
    """List all registered users."""
    try:
        db = DatabaseManager()
        users = db.get_all_users()
        
        if not users:
            click.echo("📭 No users registered yet")
            return
        
        click.echo(f"\n📋 Registered Users ({len(users)} total):")
        click.echo("-" * 50)
        for user in users:
            name_part = f" ({user[2]})" if user[2] else ""
            click.echo(f"ID: {user[0]} | {user[1]}{name_part}")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--max-papers', default=10, help='Maximum number of papers to fetch')
@click.option('--demo', is_flag=True, help='Demo mode - don\'t save to database')
@click.option('--method', type=click.Choice(['rule_based', 'transformer', 'api']), 
              help='Scoring method to use')
def fetch(max_papers, demo, method):
    """Fetch and score latest papers from arXiv."""
    try:
        if method:
            # Validate method requirements first
            validation = PaperScorer.validate_method(method)
            if not validation['valid']:
                click.echo(f"❌ Cannot use {method} method:")
                for error in validation['errors']:
                    click.echo(f"   • {error}")
                return
        
        client = ArxivClient()
        papers = client.fetch_recent_papers()
        
        if not papers:
            click.echo("📭 No papers found")
            return
        
        # Limit to requested number
        papers = papers[:max_papers]
        
        click.echo(f"📄 Fetched {len(papers)} papers from arXiv")
        
        # Score papers with specified or default method
        scorer = PaperScorer(method)
        method_info = scorer.get_method_info()
        click.echo(f"🧮 Using {method_info['name']} for scoring...")
        
        scored_papers = scorer.score_papers(papers)
        
        # Display results
        click.echo(f"\n🏆 Top {min(5, len(scored_papers))} Papers:")
        click.echo("=" * 60)
        
        for i, paper in enumerate(scored_papers[:5], 1):
            # Handle date formatting
            try:
                if hasattr(paper['published'], 'strftime'):
                    published_str = paper['published'].strftime('%Y-%m-%d')
                else:
                    # Try to parse and format the date
                    parsed_date = parser.parse(str(paper['published']))
                    published_str = parsed_date.strftime('%Y-%m-%d')
            except:
                published_str = str(paper['published'])
            
            click.echo(f"\n{i}. {paper['title']}")
            click.echo(f"   Score: {paper['score']:.1f}/20")
            click.echo(f"   Authors: {paper['authors']}")
            click.echo(f"   Published: {published_str}")
            click.echo(f"   URL: {paper['url']}")
        
        # Save to database if not demo mode
        if not demo:
            db = DatabaseManager()
            saved_count = 0
            for paper in scored_papers:
                if db.add_paper(paper):
                    saved_count += 1
            click.echo(f"\n💾 Saved {saved_count} new papers to database")
        else:
            click.echo(f"\n🎭 Demo mode - papers not saved to database")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--force', is_flag=True, help='Send notifications regardless of last notification time')
@click.option('--method', type=click.Choice(['rule_based', 'transformer', 'api']), 
              help='Scoring method to use for new papers')
def notify(force, method):
    """Send email notifications to registered users."""
    try:
        if method:
            # Validate method requirements first
            validation = PaperScorer.validate_method(method)
            if not validation['valid']:
                click.echo(f"❌ Cannot use {method} method:")
                for error in validation['errors']:
                    click.echo(f"   • {error}")
                return
        
        notifier = ArxivNotifier(scoring_method=method)
        
        if force:
            click.echo("🚀 Force sending notifications...")
            result = notifier.run_notifications(force=True)
        else:
            result = notifier.run_notifications()
        
        if result['success']:
            click.echo(f"✅ Notifications sent successfully!")
            click.echo(f"📧 Emails sent: {result['emails_sent']}")
            click.echo(f"📄 Papers included: {result['papers_sent']}")
            if result['new_papers']:
                click.echo(f"🆕 New papers fetched: {result['new_papers']}")
        else:
            click.echo(f"❌ Notification failed: {result['error']}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--email', required=True, help='User email address')
@click.option('--count', default=5, help='Number of top papers to send')
@click.option('--method', type=click.Choice(['rule_based', 'transformer', 'api']), 
              help='Scoring method to use')
def send_to_user(email, count, method):
    """Send top papers to a specific user."""
    try:
        if method:
            validation = PaperScorer.validate_method(method)
            if not validation['valid']:
                click.echo(f"❌ Cannot use {method} method:")
                for error in validation['errors']:
                    click.echo(f"   • {error}")
                return
        
        # Get user
        db = DatabaseManager()
        users = db.get_all_users()
        user = next((u for u in users if u[1] == email), None)
        
        if not user:
            click.echo(f"❌ User {email} not found")
            return
        
        # Get top papers
        papers = db.get_top_papers(count)
        if not papers:
            click.echo("📭 No papers found in database")
            return
        
        # Re-score if different method specified
        if method:
            scorer = PaperScorer(method)
            papers_list = [dict(zip(['id', 'title', 'authors', 'summary', 'url', 'published', 'score'], paper)) for paper in papers]
            papers_list = scorer.score_papers(papers_list)
            papers = [(p['id'], p['title'], p['authors'], p['summary'], p['url'], p['published'], p['score']) for p in papers_list]
        
        # Send email
        notifier = EmailNotifier()
        success = notifier.send_notification(user, papers)
        
        if success:
            click.echo(f"✅ Sent {len(papers)} papers to {email}")
        else:
            click.echo(f"❌ Failed to send email to {email}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def papers():
    """Show papers in the database."""
    try:
        db = DatabaseManager()
        papers = db.get_top_papers(20)
        
        if not papers:
            click.echo("📭 No papers in database")
            return
        
        click.echo(f"\n📚 Papers in Database ({len(papers)} total):")
        click.echo("=" * 60)
        
        for i, paper in enumerate(papers, 1):
            published = paper[5].strftime('%Y-%m-%d') if hasattr(paper[5], 'strftime') else str(paper[5])
            click.echo(f"\n{i}. {paper[1]}")
            click.echo(f"   Score: {paper[6]:.1f}/20")
            click.echo(f"   Authors: {paper[2]}")
            click.echo(f"   Published: {published}")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def test_email():
    """Test email configuration."""
    try:
        notifier = EmailNotifier()
        success = notifier.test_email_config()
        
        if success:
            click.echo("✅ Email configuration is working!")
        else:
            click.echo("❌ Email configuration failed")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.option('--user-id', type=int, help='Specific user ID to remove')
@click.option('--email', help='Specific user email to remove')
@click.confirmation_option(prompt='Are you sure you want to remove user(s)?')
def remove_user(user_id, email):
    """Remove a user from the database."""
    try:
        db = DatabaseManager()
        
        if user_id:
            success = db.remove_user(user_id)
            if success:
                click.echo(f"✅ Removed user with ID {user_id}")
            else:
                click.echo(f"❌ User with ID {user_id} not found")
        elif email:
            users = db.get_all_users()
            user = next((u for u in users if u[1] == email), None)
            if user:
                success = db.remove_user(user[0])
                if success:
                    click.echo(f"✅ Removed user {email}")
                else:
                    click.echo(f"❌ Failed to remove user {email}")
            else:
                click.echo(f"❌ User {email} not found")
        else:
            click.echo("❌ Please specify either --user-id or --email")
            
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
@click.confirmation_option(prompt='Are you sure you want to clear all papers?')
def clear_papers():
    """Clear all papers from the database."""
    try:
        db = DatabaseManager()
        db.clear_papers()
        click.echo("🗑️  All papers cleared from database")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def reset_notifications():
    """Reset notification timestamps for all users."""
    try:
        db = DatabaseManager()
        db.reset_all_notification_timestamps()
        click.echo("🔄 Reset notification timestamps for all users")
    except Exception as e:
        click.echo(f"❌ Error: {e}")

# New scoring method commands
@cli.command()
def scoring_methods():
    """Compare available paper scoring methods."""
    click.echo("🧮 Available Paper Scoring Methods:")
    PaperScorer.compare_methods()
    
    recommendations = PaperScorer.get_recommendations()
    click.echo("💡 Recommendations:")
    click.echo("-" * 40)
    for use_case, method in recommendations.items():
        click.echo(f"   {use_case.replace('_', ' ').title()}: {method}")

@cli.command()
@click.argument('method', type=click.Choice(['rule_based', 'transformer', 'api']))
def validate_method(method):
    """Validate if a scoring method can be used."""
    click.echo(f"🔍 Validating {method} scoring method...")
    
    validation = PaperScorer.validate_method(method)
    
    if validation['valid']:
        click.echo("✅ Method is ready to use!")
        method_info = ScorerFactory.get_available_methods()[method]
        click.echo(f"📝 {method_info['description']}")
        click.echo(f"💰 Cost: {method_info['cost']}")
        click.echo(f"⚡ Speed: {method_info['speed']}")
        click.echo(f"🎯 Accuracy: {method_info['accuracy']}")
    else:
        click.echo("❌ Method validation failed:")
        for error in validation['errors']:
            click.echo(f"   • {error}")
        
        if validation['warnings']:
            click.echo("⚠️  Warnings:")
            for warning in validation['warnings']:
                click.echo(f"   • {warning}")

@cli.command()
@click.argument('method', type=click.Choice(['rule_based', 'transformer', 'api']))
@click.option('--count', default=5, help='Number of papers to test with')
def test_scoring(method, count):
    """Test a specific scoring method with sample papers."""
    try:
        # Validate method first
        validation = PaperScorer.validate_method(method)
        if not validation['valid']:
            click.echo(f"❌ Cannot test {method} method:")
            for error in validation['errors']:
                click.echo(f"   • {error}")
            return
        
        # Get some papers from database or fetch new ones
        db = DatabaseManager()
        papers = db.get_top_papers(count)
        
        if not papers:
            click.echo("📄 No papers in database, fetching from arXiv...")
            client = ArxivClient()
            paper_dicts = client.fetch_recent_papers()
            if not paper_dicts:
                click.echo("❌ Could not fetch papers for testing")
                return
            # Limit to requested count
            paper_dicts = paper_dicts[:count]
        else:
            # Convert database format to dict format
            paper_dicts = []
            for paper in papers:
                paper_dicts.append({
                    'id': paper[0],
                    'title': paper[1],
                    'authors': paper[2],
                    'summary': paper[3],
                    'url': paper[4],
                    'published': paper[5],
                    'score': paper[6]
                })
            # Limit to requested count
            paper_dicts = paper_dicts[:count]
        
        # Test the scoring method
        click.echo(f"🧪 Testing {method} scoring method with {len(paper_dicts)} papers...")
        
        scorer = PaperScorer(method)
        method_info = scorer.get_method_info()
        click.echo(f"📊 Using: {method_info['name']}")
        
        scored_papers = scorer.score_papers(paper_dicts)
        
        # Show results
        click.echo(f"\n🏆 Scoring Results:")
        click.echo("=" * 60)
        
        for i, paper in enumerate(scored_papers, 1):
            # Handle date formatting
            try:
                if hasattr(paper['published'], 'strftime'):
                    published_str = paper['published'].strftime('%Y-%m-%d')
                else:
                    # Try to parse and format the date
                    parsed_date = parser.parse(str(paper['published']))
                    published_str = parsed_date.strftime('%Y-%m-%d')
            except:
                published_str = str(paper['published'])
            
            click.echo(f"\n{i}. {paper['title'][:60]}...")
            click.echo(f"   Score: {paper['score']:.1f}/20")
            click.echo(f"   Published: {published_str}")
        
        avg_score = sum(p['score'] for p in scored_papers) / len(scored_papers)
        click.echo(f"\n📈 Average Score: {avg_score:.1f}/20")
        
    except Exception as e:
        click.echo(f"❌ Error: {e}")

@cli.command()
def run():
    """Run a complete update cycle (fetch papers + send notifications)."""
    notifier = ArxivNotifier()
    
    click.echo("🚀 Starting full update cycle...")
    results = notifier.run_full_update()
    
    if 'error' in results:
        click.echo(f"❌ Update failed: {results['error']}")
        return
    
    click.echo(f"✅ Update cycle completed in {results['duration']:.1f}s")
    click.echo(f"   📄 Papers updated: {results['papers_updated']}")
    click.echo(f"   📧 Notifications sent: {results['notifications']['emails_sent']}")

@cli.command()
@click.option('--limit', default=10, help='Number of papers to show')
@click.option('--min-score', default=None, type=float, help='Minimum score threshold')
def top(limit, min_score):
    """Show top-scored papers."""
    notifier = ArxivNotifier()
    
    papers = notifier.get_top_papers(limit, min_score)
    
    if not papers:
        click.echo("No papers found matching criteria")
        return
    
    click.echo(f"🏆 Top {len(papers)} papers:")
    click.echo()
    
    for i, paper in enumerate(papers, 1):
        published = datetime.fromisoformat(paper['published'].replace('Z', '+00:00')) if isinstance(paper['published'], str) else paper['published']
        click.echo(f"{i}. {paper['title']}")
        click.echo(f"   📊 Score: {paper['score']:.1f} | 📅 {published.strftime('%Y-%m-%d')}")
        click.echo(f"   👥 {paper['authors']}")
        click.echo(f"   🔗 {paper['url']}")
        click.echo()

@cli.command()
def stats():
    """Show system statistics."""
    notifier = ArxivNotifier()
    
    user_count = notifier.get_user_count()
    top_papers = notifier.get_top_papers(5)
    
    click.echo("📊 System Statistics:")
    click.echo(f"   👥 Active users: {user_count}")
    click.echo(f"   📄 Papers in database: {len(notifier.get_top_papers(1000))}")
    click.echo(f"   🏆 Top paper score: {top_papers[0]['score']:.1f}" if top_papers else "   📄 No papers yet")
    click.echo(f"   ⏰ Update frequency: every {Config.UPDATE_FREQUENCY} hours")

@cli.command()
@click.option('--interval', default=Config.UPDATE_FREQUENCY, help='Update interval in hours')
def scheduler(interval):
    """Run the scheduler to automatically update papers and send notifications."""
    notifier = ArxivNotifier()
    
    click.echo(f"⏰ Starting scheduler with {interval}-hour intervals...")
    click.echo("   Press Ctrl+C to stop")
    
    # Schedule the job
    schedule.every(interval).hours.do(notifier.run_full_update)
    
    # Run initial update
    click.echo("🚀 Running initial update...")
    notifier.run_full_update()
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        click.echo("\n👋 Scheduler stopped")

@cli.command()
def demo():
    """Run a demo showing how the system works without email."""
    notifier = ArxivNotifier()
    
    click.echo("🎬 Demo Mode: arXiv AI Papers Notifier")
    click.echo("=" * 50)
    
    # Show current papers
    papers = notifier.get_top_papers(3)
    if papers:
        click.echo(f"\n📄 Current top papers in database:")
        for i, paper in enumerate(papers, 1):
            published = datetime.fromisoformat(paper['published'].replace('Z', '+00:00')) if isinstance(paper['published'], str) else paper['published']
            click.echo(f"{i}. {paper['title'][:60]}...")
            click.echo(f"   📊 Score: {paper['score']:.1f} | 📅 {published.strftime('%Y-%m-%d')}")
    
    # Show what email would look like
    if papers:
        click.echo(f"\n📧 Email Preview (what users would receive):")
        click.echo("=" * 50)
        click.echo("Subject: 🤖 Top CS.AI Papers Update - 3 New Papers")
        click.echo("To: user@example.com")
        click.echo("From: your-notifier@example.com")
        click.echo("\nBody:")
        click.echo("🤖 Top CS.AI Papers Update")
        click.echo("Your curated selection of high-impact AI research")
        click.echo("")
        
        for i, paper in enumerate(papers[:3], 1):
            click.echo(f"{i}. {paper['title']}")
            click.echo(f"   Authors: {paper['authors'][:80]}...")
            click.echo(f"   Score: {paper['score']:.1f}")
            click.echo(f"   URL: {paper['url']}")
            click.echo("")
        
        click.echo("Thank you to arXiv for use of its open access interoperability.")
    
    # Show stats
    user_count = notifier.get_user_count()
    click.echo(f"\n📊 System Status:")
    click.echo(f"   👥 Registered users: {user_count}")
    click.echo(f"   📄 Papers in database: {len(notifier.get_top_papers(1000))}")
    click.echo(f"   🏆 Highest paper score: {papers[0]['score']:.1f}" if papers else "   📄 No papers yet")
    
    click.echo(f"\n✨ To enable email notifications:")
    click.echo(f"   1. Edit .env file with your email credentials")
    click.echo(f"   2. Run: python cli.py test-email")
    click.echo(f"   3. Run: python cli.py notify")

if __name__ == '__main__':
    cli() 