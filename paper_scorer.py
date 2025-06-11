import re
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from config import Config
from scorer_factory import ScorerFactory

logger = logging.getLogger(__name__)

class PaperScorer:
    """Main interface for paper scoring with multiple strategy support."""
    
    def __init__(self, method: str = None):
        """Initialize with specified scoring method."""
        self.method = method or Config.SCORING_METHOD
        self.scorer = ScorerFactory.create_scorer(self.method)
        
        # Log scoring method info
        method_info = ScorerFactory.get_available_methods()[self.method]
        logger.info(f"Using {method_info['name']} for paper scoring")
        logger.debug(f"Method details: {method_info['description']}")
    
    def score_papers(self, papers: List[Dict]) -> List[Dict]:
        """Score papers using the configured method."""
        if not papers:
            logger.warning("No papers to score")
            return []
        
        logger.info(f"Scoring {len(papers)} papers using {self.method} method")
        return self.scorer.score_papers(papers)
    
    def score_paper(self, paper: Dict) -> float:
        """Score a single paper."""
        return self.scorer.score_paper(paper)
    
    def get_method_info(self) -> Dict:
        """Get information about the current scoring method."""
        methods = ScorerFactory.get_available_methods()
        return methods.get(self.method, {})
    
    def switch_method(self, new_method: str):
        """Switch to a different scoring method."""
        validation = ScorerFactory.validate_method_requirements(new_method)
        
        if not validation['valid']:
            logger.error(f"Cannot switch to {new_method}: {validation['errors']}")
            raise ValueError(f"Invalid method {new_method}: {'; '.join(validation['errors'])}")
        
        self.method = new_method
        self.scorer = ScorerFactory.create_scorer(new_method)
        logger.info(f"Switched to {new_method} scoring method")
    
    @staticmethod
    def compare_methods():
        """Print comparison of all available methods."""
        ScorerFactory.print_comparison()
    
    @staticmethod
    def validate_method(method: str) -> Dict:
        """Validate if a method can be used."""
        return ScorerFactory.validate_method_requirements(method)
    
    @staticmethod
    def get_recommendations() -> Dict:
        """Get method recommendations for different use cases."""
        return ScorerFactory.get_recommendations()
    
    @staticmethod
    def get_available_methods() -> List[str]:
        """Get list of available scoring methods."""
        return list(ScorerFactory.get_available_methods().keys())

    def _count_keyword_matches(self, text: str, keywords: List[str]) -> int:
        """Count how many keywords appear in the text."""
        count = 0
        for keyword in keywords:
            if keyword in text:
                count += 1
        return count
    
    def _score_title(self, title: str) -> float:
        """Score the quality of a paper title."""
        score = 0.0
        title_lower = title.lower()
        
        # Prefer titles with specific claims
        if any(word in title_lower for word in ['improving', 'enhancing', 'towards', 'learning']):
            score += 0.5
        
        # Penalize very short or very long titles
        word_count = len(title.split())
        if 5 <= word_count <= 15:
            score += 0.5
        elif word_count < 3 or word_count > 20:
            score -= 0.5
        
        # Bonus for specific methodological terms
        if any(word in title_lower for word in ['neural', 'learning', 'deep', 'network']):
            score += 0.5
        
        # Bonus for mathematical/theoretical indicators
        if any(char in title for char in [':', '?', '-']):
            score += 0.3
        
        return max(0.0, min(score, 2.0))
    
    def _score_abstract(self, abstract: str) -> float:
        """Score the quality of a paper abstract."""
        score = 0.0
        
        # Prefer abstracts of reasonable length
        word_count = len(abstract.split())
        if 50 <= word_count <= 300:
            score += 1.0
        elif word_count < 30:
            score -= 0.5
        
        # Look for structure indicators
        abstract_lower = abstract.lower()
        structure_words = ['we', 'our', 'propose', 'present', 'show', 'demonstrate', 
                          'results', 'experiments', 'evaluation', 'compared', 'outperform']
        structure_count = sum(1 for word in structure_words if word in abstract_lower)
        score += min(structure_count * 0.1, 1.0)
        
        return max(0.0, min(score, 2.0)) 