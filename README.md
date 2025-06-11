# 🤖 TopPapersAI

Automatically get the best CS.AI papers from arXiv delivered to your email. Stay updated with top research without the noise.

## ✨ Features

- 📧 **Email notifications** with top-rated papers
- 🤖 **3 scoring methods**: Rule-based, Transformer, or API (ChatGPT/Claude/Gemini)
- ⚡ **Easy setup** - works in 5 minutes
- 🔒 **Privacy-focused** - your data stays local

## 🚀 Quick Start

```bash
# Install
git clone https://github.com/Kevin-Li-2025/TopPapersAI.git
cd TopPapersAI
pip install -r requirements.txt

# Configure email (copy example and edit)
cp env_example.txt .env
# Edit .env with your email settings

# Register yourself
python3 cli.py register --email your@email.com --name "Your Name"

# Get papers!
python3 cli.py notify
```

## ⚙️ Main Commands

```bash
python3 cli.py register --email user@example.com    # Add new user
python3 cli.py notify                               # Send latest papers
python3 cli.py papers                               # View available papers
python3 cli.py users                                # List users
python3 cli.py scoring-methods                      # Compare scoring options
```

## 📧 Email Setup (Gmail)

1. Enable 2-Factor Authentication
2. Generate App Password: [Google Account Settings](https://myaccount.google.com) → Security → App Passwords
3. Update `.env`:
   ```
   EMAIL_FROM=your@gmail.com
   EMAIL_PASSWORD=your_16_char_app_password
   ```

## 🎯 Scoring Methods

| Method | Speed | Cost | Accuracy |
|--------|-------|------|----------|
| **Rule-based** | ⚡ Fast | 🆓 Free | ✅ Good |
| **Transformer** | 🐌 Medium | 🆓 Free | ✅✅ Better |
| **API** | 🐌 Slow | 💰 Paid | ✅✅✅ Best |

Switch anytime: `python3 cli.py notify --method transformer`

## 🔧 Configuration

Edit `.env` for your settings:
```env
# Required
EMAIL_FROM=your@email.com
EMAIL_PASSWORD=your_app_password

# Optional  
SCORING_METHOD=rule-based    # rule-based, transformer, or api
MIN_SCORE_THRESHOLD=6.0      # Minimum score for "top" papers
UPDATE_FREQUENCY=24          # Hours between updates
```

## 🤝 arXiv Compliance

✅ Non-commercial use  
✅ Proper attribution  
✅ Respectful API usage  

*"Thank you to arXiv for use of its open access interoperability."*

## 🆘 Need Help?

- 📧 **Email not working?** Check if you're using App Password (not regular password)
- 🔍 **No papers found?** Try: `python3 cli.py papers` to see what's available
- ⚡ **Want better scores?** Try: `python3 cli.py notify --method transformer`

---

**Made with ❤️ for researchers. Star ⭐ if this helps you stay updated with AI research!** 