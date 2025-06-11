import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # arXiv API settings
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ARXIV_CATEGORY = "cat:cs.AI"
    MAX_RESULTS = 50
    
    # Email settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_FROM = os.getenv("EMAIL_FROM", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    
    # Database
    DATABASE_PATH = "arxiv_notifier.db"
    
    # Update frequency (in hours)
    UPDATE_FREQUENCY = int(os.getenv("UPDATE_FREQUENCY", "24"))
    
    # Paper ranking settings
    MIN_SCORE_THRESHOLD = 5  # Minimum score for "top" papers
    DAYS_TO_CHECK = 7  # Check papers from last N days
    
    # Scoring method selection
    SCORING_METHOD = os.getenv("SCORING_METHOD", "rule_based")  # rule_based, transformer, api
    
    # API-based scoring settings
    API_PROVIDER = os.getenv("API_PROVIDER", "openai")  # openai, anthropic, deepseek, google, xai
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    XAI_API_KEY = os.getenv("XAI_API_KEY", "")
    
    # Transformer-based scoring settings
    TRANSFORMER_MODEL = os.getenv("TRANSFORMER_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    USE_SCIBERT = os.getenv("USE_SCIBERT", "false").lower() == "true"
    
    # Attribution text as required by arXiv
    ATTRIBUTION_TEXT = "Thank you to arXiv for use of its open access interoperability." 