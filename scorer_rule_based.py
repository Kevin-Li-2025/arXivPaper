from scorer_base import PaperScorerBase
from datetime import datetime
from typing import Dict, List
from config import Config
import logging
from dateutil import parser

logger = logging.getLogger(__name__)

class RuleBasedScorer(PaperScorerBase):
    """Fast, free rule-based scoring using keyword matching and heuristics."""
    
    def __init__(self):
        super().__init__()
        
        # Keywords that indicate high-impact research
        self.high_impact_keywords = [
            'state-of-the-art', 'sota', 'breakthrough', 'novel', 'first', 'new',
            'improved', 'better', 'best', 'optimal', 'efficient', 'effective',
            'significant', 'major', 'substantial', 'remarkable', 'outstanding',
            'superior', 'advanced', 'innovative', 'cutting-edge', 'pioneering'
        ]
        
        # Popular AI/ML domains and techniques
        self.trending_topics = [
            'transformer', 'attention', 'bert', 'gpt', 'llm', 'large language model',
            'neural network', 'deep learning', 'machine learning', 'reinforcement learning',
            'computer vision', 'natural language processing', 'nlp', 'generative ai',
            'diffusion', 'gan', 'variational autoencoder', 'federated learning',
            'meta-learning', 'few-shot', 'zero-shot', 'self-supervised',
            'multimodal', 'foundation model', 'pre-trained', 'fine-tuning'
        ]
        
        # Research quality indicators
        self.quality_indicators = [
            'experiment', 'evaluation', 'benchmark', 'dataset', 'baseline',
            'comparison', 'analysis', 'ablation', 'empirical', 'theoretical',
            'proof', 'theorem', 'algorithm', 'method', 'approach', 'framework'
        ]
        
        # Conference/venue indicators
        self.top_venues = [
            'neurips', 'icml', 'iclr', 'aaai', 'ijcai', 'cvpr', 'iccv', 'eccv',
            'acl', 'emnlp', 'naacl', 'icra', 'iros', 'kdd', 'www', 'sigir'
        ]
    
    def score_paper(self, paper: Dict) -> float:
        """Calculate a score for a paper based on keyword matching and heuristics."""
        score = 0.0
        
        # Combine title and abstract for analysis
        text_content = f"{paper['title']} {paper['summary']}".lower()
        
        # 1. High-impact keywords (0-3 points)
        impact_score = self._count_keyword_matches(text_content, self.high_impact_keywords)
        score += min(impact_score * 0.5, 3.0)
        
        # 2. Trending topics (0-4 points)
        trending_score = self._count_keyword_matches(text_content, self.trending_topics)
        score += min(trending_score * 0.3, 4.0)
        
        # 3. Research quality indicators (0-3 points)
        quality_score = self._count_keyword_matches(text_content, self.quality_indicators)
        score += min(quality_score * 0.2, 3.0)
        
        # 4. Recency boost (0-2 points)
        try:
            if hasattr(paper['published'], 'replace'):
                # DateTime object
                paper_date = paper['published'].replace(tzinfo=None)
            else:
                # String or other format - try to parse
                paper_date = parser.parse(str(paper['published'])).replace(tzinfo=None)
            
            days_old = (datetime.now() - paper_date).days
            if days_old <= 1:
                score += 2.0
            elif days_old <= 3:
                score += 1.5
            elif days_old <= 7:
                score += 1.0
        except Exception as e:
            # If date parsing fails, give a small penalty
            score += 0.5
        
        # 5. Title quality (0-2 points)
        title_score = self._score_title(paper['title'])
        score += title_score
        
        # 6. Abstract length and quality (0-2 points)
        abstract_score = self._score_abstract(paper['summary'])
        score += abstract_score
        
        # 7. Author count bonus (0-1 point)
        author_count = len(paper['authors'].split(', ')) if paper['authors'] else 1
        if 2 <= author_count <= 8:
            score += 0.5
        elif author_count > 8:
            score += 1.0
        
        # 8. Top venue mention bonus (0-2 points)
        venue_score = self._count_keyword_matches(text_content, self.top_venues)
        score += min(venue_score * 2.0, 2.0)
        
        return score
    
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