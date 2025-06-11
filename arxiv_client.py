import requests
import feedparser
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dateutil import parser as date_parser
from config import Config

logger = logging.getLogger(__name__)

class ArxivClient:
    def __init__(self):
        self.api_url = Config.ARXIV_API_URL
        self.category = Config.ARXIV_CATEGORY
        self.max_results = Config.MAX_RESULTS
    
    def fetch_recent_papers(self, days_back: int = Config.DAYS_TO_CHECK) -> List[Dict]:
        """Fetch recent CS.AI papers from arXiv."""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Calculate date range
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days_back)
                
                # Build query parameters - start with smaller batch for testing
                params = {
                    'search_query': self.category,
                    'start': 0,
                    'max_results': min(self.max_results, 20),  # Start smaller
                    'sortBy': 'submittedDate',
                    'sortOrder': 'descending'
                }
                
                logger.info(f"Fetching papers from arXiv API (attempt {attempt + 1}/{max_retries})")
                
                headers = {
                    'User-Agent': 'arXiv-AI-Notifier/1.0 (non-commercial research tool)'
                }
                
                # Add delay between attempts
                if attempt > 0:
                    time.sleep(retry_delay * attempt)
                
                response = requests.get(self.api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # Parse the Atom feed
                feed = feedparser.parse(response.content)
                
                if not feed.entries:
                    logger.warning("No entries found in arXiv response")
                    continue
                
                papers = []
                for entry in feed.entries:
                    try:
                        paper = self._parse_entry(entry)
                        
                        # Filter by date (make both timezone-naive for comparison)
                        paper_date = paper['published'].replace(tzinfo=None) if paper['published'].tzinfo else paper['published']
                        if paper_date >= start_date:
                            papers.append(paper)
                        
                    except Exception as e:
                        logger.warning(f"Error parsing entry: {e}")
                        continue
                
                logger.info(f"Fetched {len(papers)} recent papers")
                return papers
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Network error on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch papers after {max_retries} attempts")
                    return []
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error fetching papers: {e}")
                return []
        
        return []
    
    def _parse_entry(self, entry) -> Dict:
        """Parse a single arXiv entry."""
        # Extract paper ID from the URL
        paper_id = entry.id.split('/')[-1]
        
        # Parse published date
        published = date_parser.parse(entry.published)
        
        # Extract authors
        authors = []
        if hasattr(entry, 'authors'):
            authors = [author.name for author in entry.authors]
        elif hasattr(entry, 'author'):
            authors = [entry.author]
        
        # Clean summary
        summary = entry.summary.replace('\n', ' ').strip()
        
        # Build arXiv URL
        arxiv_url = f"https://arxiv.org/abs/{paper_id}"
        
        return {
            'id': paper_id,
            'title': entry.title,
            'authors': ', '.join(authors),
            'summary': summary,
            'published': published,
            'url': arxiv_url,
            'score': 0  # Will be calculated by the scoring system
        }
    
    def get_paper_details(self, paper_id: str) -> Optional[Dict]:
        """Get detailed information for a specific paper."""
        try:
            params = {
                'search_query': f'id:{paper_id}',
                'start': 0,
                'max_results': 1
            }
            
            headers = {
                'User-Agent': 'arXiv-AI-Notifier/1.0 (https://github.com/user/arxiv-notifier; contact@example.com)'
            }
            response = requests.get(self.api_url, params=params, headers=headers, timeout=60)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if feed.entries:
                return self._parse_entry(feed.entries[0])
            
        except Exception as e:
            logger.error(f"Error fetching paper details for {paper_id}: {e}")
        
        return None 