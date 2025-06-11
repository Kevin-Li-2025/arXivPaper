from abc import ABC, abstractmethod
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class PaperScorerBase(ABC):
    """Abstract base class for paper scoring strategies."""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.max_score = 20.0  # Maximum possible score
    
    @abstractmethod
    def score_paper(self, paper: Dict) -> float:
        """Score a single paper. Must return a score between 0 and max_score."""
        pass
    
    def score_papers(self, papers: List[Dict]) -> List[Dict]:
        """Score a list of papers and return them sorted by score."""
        logger.info(f"Scoring {len(papers)} papers using {self.name}")
        
        for paper in papers:
            try:
                paper['score'] = self.score_paper(paper)
                # Ensure score is within bounds
                paper['score'] = max(0.0, min(paper['score'], self.max_score))
                paper['score'] = round(paper['score'], 2)
            except Exception as e:
                logger.error(f"Error scoring paper {paper.get('id', 'unknown')}: {e}")
                paper['score'] = 0.0
        
        # Sort by score (descending)
        papers.sort(key=lambda x: x['score'], reverse=True)
        
        top_score = papers[0]['score'] if papers else 0
        logger.info(f"Scoring complete. Top score: {top_score:.2f}")
        
        return papers
    
    def get_info(self) -> Dict:
        """Return information about this scoring method."""
        return {
            'name': self.name,
            'max_score': self.max_score,
            'description': self.__doc__ or "No description available"
        } 