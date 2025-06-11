from scorer_base import PaperScorerBase
from scorer_rule_based import RuleBasedScorer
from scorer_transformer import TransformerScorer
from scorer_api import APIScorer
from config import Config
import logging
from typing import Dict, List, Type

logger = logging.getLogger(__name__)

class ScorerFactory:
    """Factory class for creating paper scoring instances."""
    
    AVAILABLE_SCORERS = {
        'rule_based': {
            'class': RuleBasedScorer,
            'name': 'Rule-Based Scorer',
            'description': 'Fast, free scoring using keyword matching and heuristics',
            'cost': 'Free',
            'speed': 'Very Fast',
            'accuracy': 'Good',
            'requirements': 'None'
        },
        'transformer': {
            'class': TransformerScorer,
            'name': 'Transformer Scorer',
            'description': 'Local ML-based scoring using sentence transformers',
            'cost': 'Free (after download)',
            'speed': 'Medium',
            'accuracy': 'Very Good',
            'requirements': 'sentence-transformers, torch (optional: transformers for SciBERT)'
        },
        'api': {
            'class': APIScorer,
            'name': 'API Scorer',
            'description': 'High-quality scoring using state-of-the-art LLMs',
            'cost': 'API costs apply',
            'speed': 'Slow',
            'accuracy': 'Excellent',
            'requirements': 'API keys (openai, anthropic, google-generativeai, etc.)'
        }
    }
    
    @classmethod
    def create_scorer(cls, method: str = None) -> PaperScorerBase:
        """Create a scorer instance based on the specified method."""
        if method is None:
            method = Config.SCORING_METHOD
        
        if method not in cls.AVAILABLE_SCORERS:
            logger.error(f"Unknown scoring method: {method}")
            logger.info(f"Available methods: {list(cls.AVAILABLE_SCORERS.keys())}")
            logger.info("Falling back to rule-based scoring")
            method = 'rule_based'
        
        try:
            scorer_class = cls.AVAILABLE_SCORERS[method]['class']
            scorer = scorer_class()
            logger.info(f"Created {cls.AVAILABLE_SCORERS[method]['name']}")
            return scorer
            
        except Exception as e:
            logger.error(f"Failed to create {method} scorer: {e}")
            logger.info("Falling back to rule-based scoring")
            return RuleBasedScorer()
    
    @classmethod
    def get_available_methods(cls) -> Dict:
        """Get information about all available scoring methods."""
        return cls.AVAILABLE_SCORERS
    
    @classmethod
    def print_comparison(cls):
        """Print a comparison table of all scoring methods."""
        print("\n" + "="*80)
        print("PAPER SCORING METHODS COMPARISON")
        print("="*80)
        
        # Header
        print(f"{'Method':<15} {'Cost':<15} {'Speed':<10} {'Accuracy':<12} {'Description'}")
        print("-" * 80)
        
        # Methods
        for method_id, info in cls.AVAILABLE_SCORERS.items():
            print(f"{method_id:<15} {info['cost']:<15} {info['speed']:<10} {info['accuracy']:<12} {info['description'][:35]}...")
        
        print("-" * 80)
        print(f"Current method: {Config.SCORING_METHOD}")
        print("="*80 + "\n")
    
    @classmethod
    def validate_method_requirements(cls, method: str) -> Dict:
        """Check if requirements for a scoring method are met."""
        if method not in cls.AVAILABLE_SCORERS:
            return {'valid': False, 'errors': [f'Unknown method: {method}']}
        
        errors = []
        warnings = []
        
        try:
            if method == 'transformer':
                # Check transformer dependencies
                try:
                    import sentence_transformers
                except ImportError:
                    errors.append("sentence-transformers not installed. Run: pip install sentence-transformers")
                
                if Config.USE_SCIBERT:
                    try:
                        import transformers
                        import torch
                    except ImportError as e:
                        errors.append(f"SciBERT requires transformers and torch: {e}")
            
            elif method == 'api':
                # Check API dependencies and keys
                provider = Config.API_PROVIDER
                
                if provider == 'openai':
                    if not Config.OPENAI_API_KEY:
                        errors.append("OpenAI API key not configured")
                    try:
                        import openai
                    except ImportError:
                        errors.append("openai package not installed. Run: pip install openai")
                
                elif provider == 'anthropic':
                    if not Config.ANTHROPIC_API_KEY:
                        errors.append("Anthropic API key not configured")
                    try:
                        import anthropic
                    except ImportError:
                        errors.append("anthropic package not installed. Run: pip install anthropic")
                
                elif provider == 'deepseek':
                    if not Config.DEEPSEEK_API_KEY:
                        errors.append("DeepSeek API key not configured")
                    try:
                        import openai
                    except ImportError:
                        errors.append("openai package not installed. Run: pip install openai")
                
                elif provider == 'google':
                    if not Config.GOOGLE_API_KEY:
                        errors.append("Google API key not configured")
                    try:
                        import google.generativeai
                    except ImportError:
                        errors.append("google-generativeai package not installed. Run: pip install google-generativeai")
                
                elif provider == 'xai':
                    if not Config.XAI_API_KEY:
                        errors.append("xAI API key not configured")
                    try:
                        import openai
                    except ImportError:
                        errors.append("openai package not installed. Run: pip install openai")
                
                else:
                    errors.append(f"Unknown API provider: {provider}")
        
        except Exception as e:
            errors.append(f"Unexpected error validating {method}: {e}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    @classmethod
    def get_recommendations(cls) -> Dict:
        """Get recommendations for which scoring method to use."""
        return {
            'for_beginners': 'rule_based',
            'for_researchers': 'transformer', 
            'for_production': 'api',
            'for_cost_conscious': 'rule_based',
            'for_highest_quality': 'api',
            'for_privacy': 'transformer',
            'for_speed': 'rule_based'
        } 