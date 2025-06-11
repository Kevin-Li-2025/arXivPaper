import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict
from jinja2 import Template
from config import Config

logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.email_from = Config.EMAIL_FROM
        self.email_password = Config.EMAIL_PASSWORD
        
        # Email template
        self.template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Top CS.AI Papers Update</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .paper {
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 30px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        .paper-title {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .paper-authors {
            color: #7f8c8d;
            font-style: italic;
            margin-bottom: 10px;
        }
        .paper-summary {
            margin-bottom: 15px;
            line-height: 1.5;
        }
        .paper-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }
        .paper-score {
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
        }
        .paper-date {
            color: #6c757d;
            font-size: 14px;
        }
        .paper-link {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 8px 16px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: bold;
        }
        .footer {
            margin-top: 40px;
            padding: 20px;
            background: #f1f3f4;
            border-radius: 5px;
            text-align: center;
            font-size: 12px;
            color: #6c757d;
        }
        .unsubscribe {
            margin-top: 20px;
            font-size: 11px;
            color: #999;
        }
        @media (max-width: 600px) {
            .paper-meta {
                flex-direction: column;
                align-items: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Top Computer Science Papers Update</h1>
        <p>Your curated selection of high-impact research papers</p>
    </div>
    
    {% if papers %}
        {% for paper in papers %}
        <div class="paper">
            <div class="paper-title">{{ paper.title }}</div>
            <div class="paper-authors">{{ paper.authors }}</div>
            <div class="paper-summary">{{ paper.summary[:300] }}{% if paper.summary|length > 300 %}...{% endif %}</div>
            <div class="paper-meta">
                <div>
                    <span class="paper-score">Score: {{ "%.1f"|format(paper.score) }}</span>
                    <span class="paper-date">Published: {{ paper.published.strftime('%Y-%m-%d') if paper.published.strftime else paper.published }}</span>
                </div>
                <a href="{{ paper.url }}" class="paper-link">Read Paper →</a>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="paper">
            <p>No new top papers found since your last update. We'll keep monitoring for you!</p>
        </div>
    {% endif %}
    
    <div class="footer">
        <p><strong>{{ attribution_text }}</strong></p>
        <p>This notification system helps you stay updated with the latest high-impact research in artificial intelligence.</p>
        <div class="unsubscribe">
            <p>To unsubscribe from these notifications, reply to this email with "UNSUBSCRIBE" in the subject line.</p>
        </div>
    </div>
</body>
</html>
        """)
    
    def send_notification(self, user_email: str, user_name: str, papers: List[Dict]) -> bool:
        """Send an email notification to a user with new papers."""
        try:
            if not self.email_from or not self.email_password:
                logger.error("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Top Computer Science Papers Update - {len(papers)} New Papers"
            msg['From'] = self.email_from
            msg['To'] = user_email
            
            # Generate HTML content
            html_content = self.template.render(
                papers=papers,
                user_name=user_name or "Researcher",
                attribution_text=Config.ATTRIBUTION_TEXT
            )
            
            # Create plain text version
            text_content = self._create_text_version(papers, user_name or "Researcher")
            
            # Attach both versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Sent notification to {user_email} with {len(papers)} papers")
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification to {user_email}: {e}")
            return False
    
    def _create_text_version(self, papers: List[Dict], user_name: str) -> str:
        """Create a plain text version of the email."""
        text_lines = [
            f"Top Computer Science Papers Update",
            "=" * 50,
            f"Hello {user_name},",
            "",
            f"Here are {len(papers)} new high-impact research papers:",
            ""
        ]
        
        for i, paper in enumerate(papers, 1):
            text_lines.extend([
                f"{i}. {paper['title']}",
                f"   Authors: {paper['authors']}",
                f"   Score: {paper['score']:.1f} | Published: {paper['published'].strftime('%Y-%m-%d') if hasattr(paper['published'], 'strftime') else paper['published']}",
                f"   Summary: {paper['summary'][:200]}{'...' if len(paper['summary']) > 200 else ''}",
                f"   URL: {paper['url']}",
                ""
            ])
        
        text_lines.extend([
            "=" * 50,
            Config.ATTRIBUTION_TEXT,
            "",
            "To unsubscribe, reply with 'UNSUBSCRIBE' in the subject line."
        ])
        
        return "\n".join(text_lines)
    
    def test_connection(self) -> bool:
        """Test the email connection."""
        try:
            if not self.email_from or not self.email_password:
                logger.error("Email credentials not configured")
                print("\n❌ Email not configured!")
                print("📋 To fix this:")
                print("1. Edit the .env file")
                print("2. Set EMAIL_FROM to your email address")
                print("3. Set EMAIL_PASSWORD to your app password")
                print("\n🔑 For Gmail users:")
                print("   • Enable 2-Factor Authentication")
                print("   • Generate App Password: Google Account → Security → App Passwords")
                print("   • Use the 16-character App Password (not your regular password)")
                return False
                
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_from, self.email_password)
            
            logger.info("Email connection test successful")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Email authentication failed: {e}")
            print("\n❌ Email authentication failed!")
            print("🔍 Common fixes:")
            print("   • For Gmail: Use App Password (not regular password)")
            print("   • Check EMAIL_FROM and EMAIL_PASSWORD in .env file")
            print("   • Ensure 2-Factor Authentication is enabled (Gmail)")
            print("   • Try generating a new App Password")
            return False
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            print(f"\n❌ Email connection failed: {e}")
            print("🔍 Check your SMTP_SERVER and SMTP_PORT settings")
            return False 