# 🤖 arXiv AI Papers Notifier

An automated system that tracks top CS.AI papers from arXiv and sends email notifications to registered users. This tool helps researchers stay updated with high-impact artificial intelligence research.

## ✅ Features

- **Automated Paper Fetching**: Retrieves latest CS.AI papers from arXiv API
- **Intelligent Scoring**: Ranks papers based on multiple quality indicators
- **Email Notifications**: Beautiful HTML emails with paper summaries
- **User Management**: Easy registration and unsubscription
- **Scheduled Updates**: Automatic daily updates
- **CLI Interface**: Simple command-line tools for management

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
git clone <repository-url>
cd arxiv-ai-notifier

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your email settings:

```env
# Email Configuration (required)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

# Optional settings
UPDATE_FREQUENCY=24
MIN_SCORE_THRESHOLD=5.0
```

### 3. Register Users

```bash
# Register a new user
python cli.py register --email researcher@university.edu --name "Dr. Smith"

# Test email setup
python cli.py test-email
```

### 4. Run Updates

```bash
# Manual update
python cli.py run

# Start automated scheduler
python cli.py scheduler
```

## 📧 Email Setup

### Gmail Setup (Recommended)
1. **Enable 2-Factor Authentication** on your Google Account
2. **Generate App Password**:
   - Go to: [Google Account Settings](https://myaccount.google.com)
   - Navigate: Security → 2-Step Verification → App Passwords
   - Select "Mail" as the app type
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)
3. **Update .env file**:
   ```env
   EMAIL_FROM=youremail@gmail.com
   EMAIL_PASSWORD=abcd efgh ijkl mnop  # App Password (no spaces)
   ```
4. **Test setup**: `python cli.py test-email`

> ⚠️ **Important**: Use the App Password, NOT your regular Gmail password!

### Other Email Providers
- **Outlook**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Update `SMTP_SERVER` and `SMTP_PORT`

## 🛠️ CLI Commands

```bash
# User management
python cli.py register --email user@example.com --name "User Name"
python cli.py unsubscribe --email user@example.com

# Paper operations
python cli.py update          # Fetch new papers
python cli.py notify          # Send notifications
python cli.py run             # Full update cycle

# Information
python cli.py top --limit 5   # Show top papers
python cli.py stats           # System statistics

# System
python cli.py test-email      # Test email config
python cli.py scheduler       # Run automated updates
```

## 🎯 Paper Scoring System

Papers are scored (0-20+ points) based on:

- **High-impact keywords** (3 pts): "state-of-the-art", "novel", "breakthrough"
- **Trending topics** (4 pts): "transformer", "LLM", "deep learning"
- **Research quality** (3 pts): "experiment", "evaluation", "benchmark"
- **Recency** (2 pts): Newer papers get higher scores
- **Title quality** (2 pts): Well-structured, specific titles
- **Abstract quality** (2 pts): Appropriate length and structure
- **Collaboration** (1 pt): Multiple authors indicate collaboration
- **Top venues** (2 pts): Mentions of prestigious conferences

## 📊 Database Schema

The system uses SQLite with three main tables:
- **users**: Registered users and their preferences
- **papers**: Fetched papers with scores and metadata
- **sent_notifications**: Tracking sent notifications to avoid duplicates

## 🔧 Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `UPDATE_FREQUENCY` | Hours between updates | 24 |
| `MIN_SCORE_THRESHOLD` | Minimum score for "top" papers | 5.0 |
| `MAX_RESULTS` | Papers fetched per API call | 50 |
| `DAYS_TO_CHECK` | Look back period for papers | 7 |

## 🤝 arXiv Compliance

This project follows arXiv's API usage guidelines:
- ✅ Non-commercial use
- ✅ Independent operation
- ✅ Respectful of branding rules
- ✅ Includes required attribution

**Attribution**: "Thank you to arXiv for use of its open access interoperability."

## 📝 Example Usage

### Automated Daily Updates
```bash
# Set up cron job for daily updates at 9 AM
0 9 * * * cd /path/to/arxiv-notifier && python cli.py run
```

### Custom Deployment
```python
from arxiv_notifier import ArxivNotifier

# Initialize notifier
notifier = ArxivNotifier()

# Register users programmatically
notifier.register_user("researcher@ai-lab.edu", "Dr. AI Researcher")

# Run updates
results = notifier.run_full_update()
print(f"Sent {results['notifications']['emails_sent']} notifications")
```

## 🐛 Troubleshooting

### Email Issues
- Verify SMTP settings in `.env`
- Check firewall/antivirus blocking SMTP
- For Gmail, ensure App Password is used (not regular password)

### No Papers Found
- Check internet connection
- Verify arXiv API is accessible
- Lower `MIN_SCORE_THRESHOLD` in config

### Database Errors
- Check file permissions for `arxiv_notifier.db`
- Delete database file to reset (will lose user data)

## 🔒 Security Notes

- Store email credentials securely in `.env` file
- Use App Passwords instead of main email passwords
- Keep the `.env` file out of version control
- Consider using environment variables in production

## 📈 Future Enhancements

- Web dashboard for user management
- RSS feed generation
- Slack/Discord integrations
- Custom keyword filtering
- Citation tracking
- Multi-category support

---

**Note**: This is a non-commercial research tool that respectfully uses arXiv's open access API. Please follow arXiv's terms of service when using this system. 

# arXiv Paper Notifier 🤖📄

An intelligent notification system that automatically fetches, scores, and emails you the top CS.AI papers from arXiv. Stay up-to-date with cutting-edge research without the noise!

## 🌟 Features

- **🧮 Three Scoring Methods**: Choose between rule-based, transformer-based, or API-based scoring
- **📧 Smart Email Notifications**: Beautiful HTML emails with paper summaries
- **🔄 Automated Updates**: Configurable scheduling for paper fetching and notifications  
- **🎯 High-Quality Filtering**: Advanced scoring algorithms to surface the most impactful papers
- **🌐 Web Interface**: Clean dashboard to manage users and view papers
- **⚡ CLI Interface**: Complete command-line tool with 15+ commands
- **📊 Multiple Metrics**: Score papers on novelty, technical depth, impact, and more
- **🔒 arXiv Compliant**: Respects rate limits and includes proper attribution

## 🧮 Paper Scoring Methods

The system offers three different approaches to score papers, each with unique advantages:

### 1. Rule-Based Scoring (Default) 🚀
- **Cost**: Free
- **Speed**: Very Fast  
- **Accuracy**: Good
- **Best for**: Beginners, cost-conscious users, high-volume processing

**How it works**: Uses keyword matching, heuristics, and statistical analysis:
- High-impact keywords (0-3 pts): "state-of-the-art", "breakthrough", "novel"
- Trending topics (0-4 pts): "transformer", "attention", "deep learning" 
- Quality indicators (0-3 pts): "experiment", "evaluation", "benchmark"
- Recency boost (0-2 pts): Newer papers get higher scores
- Title/abstract quality (0-4 pts): Length, structure, clarity
- Author collaboration (0-1 pt): Optimal team sizes
- Top venues (0-2 pts): Mentions of premier conferences

### 2. Transformer-Based Scoring 🤖
- **Cost**: Free (after model download)
- **Speed**: Medium
- **Accuracy**: Very Good  
- **Best for**: Researchers, privacy-conscious users, offline usage

**How it works**: Uses local machine learning models for semantic understanding:
- Semantic similarity to high-quality reference papers (0-8 pts)
- Title-abstract coherence analysis (0-3 pts)
- Technical complexity detection (0-4 pts)
- Novelty indicators via embeddings (0-3 pts)
- Publication recency (0-2 pts)

**Models supported**:
- Sentence Transformers (default: `all-MiniLM-L6-v2`)
- SciBERT for scientific text understanding (optional)

### 3. API-Based Scoring 🎯
- **Cost**: API charges apply
- **Speed**: Slow
- **Accuracy**: Excellent
- **Best for**: Production use, highest quality results

**How it works**: Leverages state-of-the-art language models as expert reviewers:
- Technical novelty and innovation (0-5 pts)
- Methodological rigor (0-4 pts)
- Potential impact and significance (0-4 pts)
- Clarity and presentation (0-3 pts)
- Experimental validation (0-2 pts)
- Research relevance (0-2 pts)

**Supported APIs**:
- **OpenAI**: GPT-4o-mini (cost-effective)
- **Anthropic**: Claude 3 Haiku
- **DeepSeek**: DeepSeek Chat
- **Google**: Gemini 1.5 Flash
- **xAI**: Grok Beta

## 🚀 Quick Start

### Installation
```bash
git clone https://github.com/yourusername/arxiv-notifier.git
cd arxiv-notifier
pip install -r requirements.txt
```

### Basic Configuration
```bash
# Copy environment template
cp env_example.txt .env

# Edit with your settings
nano .env
```

### Choose Your Scoring Method

**Option 1: Rule-Based (No setup required)**
```bash
python3 cli.py scoring-methods  # View comparison
python3 cli.py validate-method rule_based
python3 cli.py test-scoring rule_based --count 5
```

**Option 2: Transformer-Based**
```bash
# Install additional dependencies
pip install sentence-transformers torch

# Test the method
python3 cli.py validate-method transformer
python3 cli.py test-scoring transformer --count 5
```

**Option 3: API-Based**
```bash
# Install API dependencies
pip install openai anthropic google-generativeai

# Configure API key in .env file
echo "OPENAI_API_KEY=your-key-here" >> .env
echo "API_PROVIDER=openai" >> .env
echo "SCORING_METHOD=api" >> .env

# Test the method
python3 cli.py validate-method api
python3 cli.py test-scoring api --count 5
```

### Basic Usage
```bash
# Register users
python3 cli.py register --email researcher@university.edu --name "Dr. Smith"

# Fetch and score papers
python3 cli.py fetch --max-papers 20 --method transformer

# Send notifications  
python3 cli.py notify --method api

# View results
python3 cli.py papers
```

## 📧 Email Configuration

Add to your `.env` file:
```env
# Email settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_FROM=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# Scoring method
SCORING_METHOD=rule_based  # or transformer, api
```

Test your email setup:
```bash
python3 cli.py test-email
```

## 🔧 Advanced Configuration

### Scoring Method Configuration

**Environment Variables**:
```env
# Choose scoring method
SCORING_METHOD=rule_based  # rule_based, transformer, api

# Transformer settings
TRANSFORMER_MODEL=sentence-transformers/all-MiniLM-L6-v2
USE_SCIBERT=false  # Set to true for scientific papers

# API settings  
API_PROVIDER=openai  # openai, anthropic, deepseek, google, xai
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
# ... other API keys
```

### Method Comparison
```bash
python3 cli.py scoring-methods
```

Output:
```
Method          Cost            Speed      Accuracy     Description
rule_based      Free            Very Fast  Good         Fast, free scoring using keyword ma...
transformer     Free (after download) Medium     Very Good    Local ML-based scoring using senten...
api             API costs apply Slow       Excellent    High-quality scoring using state-of...
```

### Method Validation
```bash
python3 cli.py validate-method transformer
```

Output:
```
🔍 Validating transformer scoring method...
✅ Method is ready to use!
📝 Local ML-based scoring using sentence transformers
💰 Cost: Free (after download)
⚡ Speed: Medium  
🎯 Accuracy: Very Good
```

## 🖥️ CLI Commands

### Core Commands
```bash
# User management
python3 cli.py register --email user@domain.com
python3 cli.py users
python3 cli.py remove-user --email user@domain.com

# Paper operations
python3 cli.py fetch --max-papers 20 --method transformer --demo
python3 cli.py papers
python3 cli.py clear-papers

# Notifications
python3 cli.py notify --force --method api
python3 cli.py send-to-user --email user@domain.com --count 10
python3 cli.py reset-notifications

# Scoring methods
python3 cli.py scoring-methods
python3 cli.py validate-method api
python3 cli.py test-scoring transformer --count 5

# System
python3 cli.py test-email
```

### Workflow Examples

**Daily Research Updates**:
```bash
# Morning routine for a researcher
python3 cli.py fetch --method transformer --max-papers 50
python3 cli.py notify --method transformer
```

**High-Quality Weekly Digest**:  
```bash
# Weekly high-quality paper review
python3 cli.py fetch --method api --max-papers 100
python3 cli.py send-to-user --email senior-researcher@lab.edu --count 20 --method api
```

**Fast Bulk Processing**:
```bash
# Process many papers quickly
python3 cli.py fetch --method rule_based --max-papers 200
python3 cli.py notify --force --method rule_based
```

## 🌐 Web Interface

Start the web server:
```bash
python3 web_app.py
```

Features:
- 📊 Admin dashboard with user and paper management
- 📧 Email testing interface
- 📈 Scoring method comparison
- 🔧 System configuration

Access at `http://localhost:5000`

## 📊 Performance Comparison

| Aspect | Rule-Based | Transformer | API-Based |
|--------|------------|-------------|-----------|
| **Setup Time** | Instant | 5-10 min | 2-3 min |
| **Cost per 1000 papers** | $0 | $0 | $5-20 |
| **Processing Time** | 1-2 sec | 30-60 sec | 5-10 min |
| **Quality Score** | 7/10 | 8/10 | 9/10 |
| **Internet Required** | Yes (arXiv) | Yes (arXiv only) | Yes |
| **Privacy** | Good | Excellent | Fair |

## 🏗️ Architecture

```
├── Scoring Layer
│   ├── scorer_rule_based.py     # Fast keyword-based scoring
│   ├── scorer_transformer.py   # ML-based semantic scoring  
│   ├── scorer_api.py           # LLM-based expert scoring
│   └── scorer_factory.py       # Method selection & validation
├── Core Components  
│   ├── arxiv_client.py         # arXiv API integration
│   ├── email_notifier.py       # Email delivery system
│   ├── database.py             # SQLite data management
│   └── arxiv_notifier.py       # Main orchestrator
├── Interfaces
│   ├── cli.py                  # Command-line interface (15+ commands)
│   └── web_app.py              # Web dashboard
└── Configuration
    ├── config.py               # Settings management
    └── .env                    # Environment variables
```

## 🔍 Scoring Details

### Rule-Based Algorithm
The rule-based scorer evaluates papers across 8 dimensions:

1. **High-Impact Keywords** (0-3 pts): Scans for terms like "state-of-the-art", "breakthrough"
2. **Trending Topics** (0-4 pts): Identifies hot areas like "transformer", "LLM"  
3. **Quality Indicators** (0-3 pts): Looks for "experiment", "benchmark", "evaluation"
4. **Recency Boost** (0-2 pts): Newer papers score higher (1 day = 2pts, 1 week = 1pt)
5. **Title Quality** (0-2 pts): Optimal length, clear structure, methodology terms
6. **Abstract Quality** (0-2 pts): Proper length, structural indicators
7. **Collaboration** (0-1 pt): Rewards optimal team sizes (2-8 authors)
8. **Venue Recognition** (0-2 pts): Detects mentions of top-tier conferences

### Transformer Scoring Process
1. **Embedding Generation**: Creates dense vector representations of titles/abstracts
2. **Similarity Analysis**: Compares against high-quality reference papers  
3. **Coherence Check**: Measures title-abstract semantic alignment
4. **Technical Assessment**: Identifies complexity indicators and mathematical content
5. **Novelty Detection**: Spots innovative language patterns and advancement claims

### API Scoring Workflow
1. **Prompt Engineering**: Formats paper details with expert evaluation criteria
2. **LLM Evaluation**: Sends to configured language model with structured scoring rubric
3. **Response Parsing**: Extracts numerical scores and reasoning from JSON responses
4. **Quality Assurance**: Validates scores within bounds and provides fallbacks
5. **Cost Optimization**: Uses cost-effective models (GPT-4o-mini, Claude Haiku) with rate limiting

## 🤝 Contributing

We welcome contributions! Areas for improvement:

- **New Scoring Methods**: Implement domain-specific or ensemble approaches
- **API Integrations**: Add support for more LLM providers
- **UI/UX**: Enhance web interface with charts and analytics
- **Performance**: Optimize transformer inference and API batching
- **Features**: RSS feeds, Slack notifications, mobile app

## 📜 arXiv Compliance

This tool fully complies with arXiv's terms of use:
- ✅ Non-commercial, research-focused usage
- ✅ Respectful API rate limiting with delays
- ✅ Proper attribution: "Thank you to arXiv for use of its open access interoperability"
- ✅ Independent tool, not affiliated with arXiv
- ✅ User-Agent headers identifying the tool

## 🔒 Privacy & Security

- **Local Processing**: Transformer method runs entirely offline after model download
- **API Security**: API keys stored in environment variables, not committed to git
- **Data Minimization**: Only stores paper metadata and user emails
- **No Tracking**: No analytics, cookies, or user behavior monitoring

## 📈 Use Cases

### For Individual Researchers
```bash
# Personal daily digest with high-quality scoring
python3 cli.py register --email myemail@university.edu
python3 cli.py fetch --method transformer --max-papers 30
python3 cli.py notify
```

### For Research Labs  
```bash
# Weekly high-impact paper review for team
python3 cli.py fetch --method api --max-papers 100
python3 cli.py send-to-user --email pi@lab.edu --count 15 --method api
python3 cli.py send-to-user --email postdoc@lab.edu --count 10 --method api
```

### For Paper Review Services
```bash
# Fast processing of large paper volumes
python3 cli.py fetch --method rule_based --max-papers 500
python3 cli.py papers | head -50  # View top papers
```

## 🐛 Troubleshooting

### Common Issues

**Transformer method fails**:
```bash
pip install sentence-transformers torch
python3 cli.py validate-method transformer
```

**API method shows "key not configured"**:
```bash
echo "OPENAI_API_KEY=your-actual-key" >> .env
python3 cli.py validate-method api
```

**Email sending fails**:
```bash
python3 cli.py test-email
# Check SMTP settings in .env file
```

**No papers found**:
```bash
# Check arXiv connectivity
python3 cli.py fetch --max-papers 5 --demo
```

### Debugging Commands
```bash
# Check system status
python3 cli.py scoring-methods
python3 cli.py users
python3 cli.py papers

# Test individual components
python3 cli.py test-scoring rule_based --count 3
python3 cli.py validate-method transformer
python3 cli.py test-email
```

## 📝 License

MIT License - Feel free to use and modify for research and personal projects.

## 🙏 Acknowledgments

- **arXiv** for providing open access to research papers
- **Hugging Face** for transformer models and libraries  
- **OpenAI, Anthropic, Google** for accessible AI APIs
- **Research community** for inspiration and feedback

---

**⭐ Star this repository if it helps your research!**

For questions, issues, or feature requests, please open a GitHub issue or contact the maintainers. 