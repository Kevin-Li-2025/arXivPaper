from scorer_base import PaperScorerBase
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
import logging
import numpy as np
from dateutil import parser

logger = logging.getLogger(__name__)

class TransformerScorer(PaperScorerBase):
    """Local transformer-based scoring using sentence embeddings and ML models."""
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.classifier = None
        self.reference_embeddings = None
        
        # Reference papers for similarity comparison
        self.reference_high_quality_abstracts = [
            "We present a novel transformer architecture that achieves state-of-the-art performance on multiple benchmarks.",
            "This paper introduces a new deep learning method for computer vision that outperforms existing approaches.",
            "We propose an innovative approach to natural language processing using attention mechanisms.",
            "Our work demonstrates significant improvements in reinforcement learning through novel neural network designs.",
            "This research presents groundbreaking results in machine learning with comprehensive experimental validation."
        ]
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the transformer models."""
        try:
            if Config.USE_SCIBERT:
                from transformers import AutoTokenizer, AutoModel
                model_name = "allenai/scibert_scivocab_uncased"
                logger.info(f"Initializing SciBERT model: {model_name}")
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModel.from_pretrained(model_name)
            else:
                from sentence_transformers import SentenceTransformer
                model_name = Config.TRANSFORMER_MODEL
                logger.info(f"Initializing sentence transformer: {model_name}")
                self.model = SentenceTransformer(model_name)
            
            # Pre-compute reference embeddings
            self._compute_reference_embeddings()
            logger.info("Transformer scorer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize transformer models: {e}")
            logger.warning("Falling back to simplified scoring")
            self.model = None
    
    def _compute_reference_embeddings(self):
        """Pre-compute embeddings for reference high-quality abstracts."""
        if self.model is None:
            return
        
        try:
            if Config.USE_SCIBERT:
                self.reference_embeddings = self._get_scibert_embeddings(self.reference_high_quality_abstracts)
            else:
                self.reference_embeddings = self.model.encode(self.reference_high_quality_abstracts)
            logger.info(f"Computed {len(self.reference_embeddings)} reference embeddings")
        except Exception as e:
            logger.error(f"Failed to compute reference embeddings: {e}")
            self.reference_embeddings = None
    
    def _get_scibert_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings using SciBERT."""
        import torch
        
        embeddings = []
        for text in texts:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, 
                                  padding=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use CLS token embedding
                embedding = outputs.last_hidden_state[:, 0, :].numpy()
                embeddings.append(embedding[0])
        
        return np.array(embeddings)
    
    def score_paper(self, paper: Dict) -> float:
        """Score a paper using transformer-based methods."""
        if self.model is None:
            # Fallback to simple heuristic scoring
            return self._fallback_scoring(paper)
        
        try:
            score = 0.0
            
            # 1. Semantic similarity to high-quality papers (0-8 points)
            similarity_score = self._compute_similarity_score(paper)
            score += similarity_score
            
            # 2. Title-abstract coherence (0-3 points)
            coherence_score = self._compute_coherence_score(paper)
            score += coherence_score
            
            # 3. Technical complexity indicators (0-4 points)
            complexity_score = self._compute_complexity_score(paper)
            score += complexity_score
            
            # 4. Novelty indicators (0-3 points)
            novelty_score = self._compute_novelty_score(paper)
            score += novelty_score
            
            # 5. Recency boost (0-2 points)
            recency_score = self._compute_recency_score(paper)
            score += recency_score
            
            return score
            
        except Exception as e:
            logger.error(f"Error in transformer scoring: {e}")
            return self._fallback_scoring(paper)
    
    def _compute_similarity_score(self, paper: Dict) -> float:
        """Compute similarity to high-quality reference papers."""
        if self.reference_embeddings is None:
            return 0.0
        
        try:
            # Get embedding for this paper's abstract
            abstract = paper['summary']
            if Config.USE_SCIBERT:
                paper_embedding = self._get_scibert_embeddings([abstract])[0]
            else:
                paper_embedding = self.model.encode([abstract])[0]
            
            # Compute cosine similarities to reference papers
            similarities = []
            for ref_embedding in self.reference_embeddings:
                similarity = np.dot(paper_embedding, ref_embedding) / (
                    np.linalg.norm(paper_embedding) * np.linalg.norm(ref_embedding)
                )
                similarities.append(similarity)
            
            # Use maximum similarity
            max_similarity = max(similarities)
            
            # Scale to 0-8 points
            return min(max_similarity * 8.0, 8.0)
            
        except Exception as e:
            logger.error(f"Error computing similarity score: {e}")
            return 0.0
    
    def _compute_coherence_score(self, paper: Dict) -> float:
        """Compute coherence between title and abstract."""
        try:
            title = paper['title']
            abstract = paper['summary']
            
            if Config.USE_SCIBERT:
                embeddings = self._get_scibert_embeddings([title, abstract])
                title_emb, abstract_emb = embeddings[0], embeddings[1]
            else:
                title_emb, abstract_emb = self.model.encode([title, abstract])
            
            # Compute cosine similarity
            similarity = np.dot(title_emb, abstract_emb) / (
                np.linalg.norm(title_emb) * np.linalg.norm(abstract_emb)
            )
            
            # Scale to 0-3 points
            return min(similarity * 3.0, 3.0)
            
        except Exception as e:
            logger.error(f"Error computing coherence score: {e}")
            return 0.0
    
    def _compute_complexity_score(self, paper: Dict) -> float:
        """Score based on technical complexity indicators."""
        score = 0.0
        text = f"{paper['title']} {paper['summary']}".lower()
        
        # Technical terms that indicate complexity
        technical_terms = [
            'algorithm', 'optimization', 'mathematical', 'theoretical', 'proof',
            'convergence', 'complexity', 'approximation', 'polynomial', 'exponential',
            'gradient', 'backpropagation', 'neural', 'architecture', 'attention',
            'transformer', 'convolutional', 'recurrent', 'generative', 'discriminative'
        ]
        
        # Count technical terms
        term_count = sum(1 for term in technical_terms if term in text)
        score += min(term_count * 0.3, 2.0)
        
        # Mathematical notation indicators
        math_indicators = ['equation', 'formula', 'theorem', 'lemma', 'proposition']
        math_count = sum(1 for indicator in math_indicators if indicator in text)
        score += min(math_count * 0.5, 2.0)
        
        return min(score, 4.0)
    
    def _compute_novelty_score(self, paper: Dict) -> float:
        """Score based on novelty indicators."""
        score = 0.0
        text = f"{paper['title']} {paper['summary']}".lower()
        
        # Novelty keywords
        novelty_terms = [
            'novel', 'new', 'first', 'introduce', 'propose', 'present',
            'innovative', 'breakthrough', 'pioneering', 'unprecedented',
            'original', 'unique', 'distinctive', 'groundbreaking'
        ]
        
        novelty_count = sum(1 for term in novelty_terms if term in text)
        score += min(novelty_count * 0.4, 2.0)
        
        # Comparison terms (indicating advancement)
        comparison_terms = [
            'outperform', 'better than', 'superior', 'improve', 'enhance',
            'exceed', 'surpass', 'advance', 'progress', 'state-of-the-art'
        ]
        
        comparison_count = sum(1 for term in comparison_terms if term in text)
        score += min(comparison_count * 0.3, 1.0)
        
        return min(score, 3.0)
    
    def _compute_recency_score(self, paper: Dict) -> float:
        """Score based on publication recency."""
        try:
            # Handle different date formats
            if hasattr(paper['published'], 'replace'):
                # DateTime object
                paper_date = paper['published'].replace(tzinfo=None)
            else:
                # String or other format - try to parse
                paper_date = parser.parse(str(paper['published'])).replace(tzinfo=None)
            
            days_old = (datetime.now() - paper_date).days
            
            if days_old <= 1:
                return 2.0
            elif days_old <= 3:
                return 1.5
            elif days_old <= 7:
                return 1.0
            elif days_old <= 14:
                return 0.5
            else:
                return 0.0
        except Exception as e:
            logger.error(f"Error computing recency score: {e}")
            return 0.5  # Default moderate score if date parsing fails
    
    def _fallback_scoring(self, paper: Dict) -> float:
        """Simple fallback scoring when transformer models fail."""
        score = 0.0
        text = f"{paper['title']} {paper['summary']}".lower()
        
        # Simple keyword-based scoring
        important_keywords = [
            'neural', 'learning', 'deep', 'transformer', 'attention',
            'novel', 'new', 'state-of-the-art', 'performance', 'results'
        ]
        
        keyword_count = sum(1 for keyword in important_keywords if keyword in text)
        score += min(keyword_count * 1.0, 10.0)
        
        # Recency bonus
        try:
            if hasattr(paper['published'], 'replace'):
                paper_date = paper['published'].replace(tzinfo=None)
            else:
                paper_date = parser.parse(str(paper['published'])).replace(tzinfo=None)
            
            days_old = (datetime.now() - paper_date).days
            if days_old <= 7:
                score += 5.0
        except:
            score += 2.0  # Default bonus if date parsing fails
        
        return min(score, 20.0) 