from scorer_base import PaperScorerBase
from datetime import datetime
from typing import Dict, List, Optional
from config import Config
import logging
import json
import time
from dateutil import parser

logger = logging.getLogger(__name__)

class APIScorer(PaperScorerBase):
    """High-quality API-based scoring using state-of-the-art language models."""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.provider = Config.API_PROVIDER
        self._initialize_client()
        
        # Scoring prompt template
        self.scoring_prompt = """
You are an expert AI researcher evaluating the quality and impact of academic papers in AI/ML. 

Please score this paper on a scale of 0-20 based on the following criteria:
- Technical novelty and innovation (0-5 points)
- Methodological rigor and soundness (0-4 points) 
- Potential impact and significance (0-4 points)
- Clarity and presentation quality (0-3 points)
- Experimental validation and results (0-2 points)
- Relevance to current AI research (0-2 points)

Paper Details:
Title: {title}
Authors: {authors}
Abstract: {abstract}
Published: {published}

Provide your response in this exact JSON format:
{{
    "score": <number between 0-20>,
    "reasoning": "<brief explanation of your scoring>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "weaknesses": ["<weakness 1>", "<weakness 2>"]
}}
"""
    
    def _initialize_client(self):
        """Initialize the API client based on the configured provider."""
        try:
            if self.provider == "openai":
                self._init_openai()
            elif self.provider == "anthropic":
                self._init_anthropic()
            elif self.provider == "deepseek":
                self._init_deepseek()
            elif self.provider == "google":
                self._init_google()
            elif self.provider == "xai":
                self._init_xai()
            else:
                raise ValueError(f"Unsupported API provider: {self.provider}")
                
            logger.info(f"Initialized {self.provider} API client for scoring")
            
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} API client: {e}")
            self.client = None
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        if not Config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not configured")
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
            self.model_name = "gpt-4o-mini"  # Cost-effective option
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def _init_anthropic(self):
        """Initialize Anthropic Claude client."""
        if not Config.ANTHROPIC_API_KEY:
            raise ValueError("Anthropic API key not configured")
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
            self.model_name = "claude-3-haiku-20240307"  # Cost-effective option
        except ImportError:
            raise ImportError("Anthropic package not installed. Run: pip install anthropic")
    
    def _init_deepseek(self):
        """Initialize DeepSeek client."""
        if not Config.DEEPSEEK_API_KEY:
            raise ValueError("DeepSeek API key not configured")
        
        try:
            import openai  # DeepSeek uses OpenAI-compatible API
            self.client = openai.OpenAI(
                api_key=Config.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com"
            )
            self.model_name = "deepseek-chat"
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def _init_google(self):
        """Initialize Google Gemini client."""
        if not Config.GOOGLE_API_KEY:
            raise ValueError("Google API key not configured")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            self.model_name = "gemini-1.5-flash"
        except ImportError:
            raise ImportError("Google GenerativeAI package not installed. Run: pip install google-generativeai")
    
    def _init_xai(self):
        """Initialize xAI Grok client."""
        if not Config.XAI_API_KEY:
            raise ValueError("xAI API key not configured")
        
        try:
            import openai  # xAI uses OpenAI-compatible API
            self.client = openai.OpenAI(
                api_key=Config.XAI_API_KEY,
                base_url="https://api.x.ai/v1"
            )
            self.model_name = "grok-beta"
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
    
    def score_paper(self, paper: Dict) -> float:
        """Score a paper using API-based evaluation."""
        if self.client is None:
            logger.warning("API client not available, using fallback scoring")
            return self._fallback_scoring(paper)
        
        try:
            # Format the prompt with proper date handling
            try:
                if hasattr(paper['published'], 'strftime'):
                    published_str = paper['published'].strftime('%Y-%m-%d')
                else:
                    # Try to parse and format the date
                    parsed_date = parser.parse(str(paper['published']))
                    published_str = parsed_date.strftime('%Y-%m-%d')
            except:
                published_str = str(paper['published'])
            
            prompt = self.scoring_prompt.format(
                title=paper['title'],
                authors=paper['authors'],
                abstract=paper['summary'],
                published=published_str
            )
            
            # Get API response
            response = self._make_api_call(prompt)
            
            # Parse the response
            return self._parse_response(response, paper)
            
        except Exception as e:
            logger.error(f"Error in API scoring for paper {paper.get('id', 'unknown')}: {e}")
            return self._fallback_scoring(paper)
    
    def _make_api_call(self, prompt: str) -> str:
        """Make API call based on the configured provider."""
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=1000,
                    temperature=0.1,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.provider in ["deepseek", "xai"]:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                return response.choices[0].message.content
            
            elif self.provider == "google":
                response = self.client.generate_content(prompt)
                return response.text
            
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"API call failed: {e}")
            # Rate limiting handling
            if "rate limit" in str(e).lower():
                logger.info("Rate limited, waiting 60 seconds...")
                time.sleep(60)
                return self._make_api_call(prompt)  # Retry once
            raise
    
    def _parse_response(self, response: str, paper: Dict) -> float:
        """Parse the API response and extract the score."""
        try:
            # Try to extract JSON from the response
            response_clean = response.strip()
            
            # Find JSON in the response
            start_idx = response_clean.find('{')
            end_idx = response_clean.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning("No JSON found in API response, using text parsing")
                return self._parse_text_response(response)
            
            json_str = response_clean[start_idx:end_idx]
            parsed = json.loads(json_str)
            
            score = float(parsed.get('score', 0))
            reasoning = parsed.get('reasoning', 'No reasoning provided')
            
            # Log the evaluation details
            logger.info(f"API scored paper '{paper['title'][:50]}...' -> {score:.1f}/20")
            logger.debug(f"Reasoning: {reasoning}")
            
            return min(max(score, 0.0), 20.0)  # Ensure score is in valid range
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return self._parse_text_response(response)
    
    def _parse_text_response(self, response: str) -> float:
        """Fallback text parsing when JSON parsing fails."""
        try:
            # Look for score patterns in text
            import re
            
            # Pattern: "score: 15" or "Score: 15" or "15/20" etc.
            patterns = [
                r'score[:\s]+(\d+\.?\d*)',
                r'(\d+\.?\d*)[/\s]*(?:out of\s*)?20',
                r'rating[:\s]+(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*points?'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.lower())
                if matches:
                    score = float(matches[0])
                    return min(max(score, 0.0), 20.0)
            
            # If no patterns found, return a moderate score
            logger.warning("Could not extract score from API response, returning default")
            return 10.0
            
        except Exception as e:
            logger.error(f"Error parsing text response: {e}")
            return 5.0
    
    def _fallback_scoring(self, paper: Dict) -> float:
        """Simple fallback scoring when API is unavailable."""
        score = 0.0
        text = f"{paper['title']} {paper['summary']}".lower()
        
        # Basic keyword scoring
        high_quality_keywords = [
            'novel', 'state-of-the-art', 'breakthrough', 'significant',
            'efficient', 'effective', 'improved', 'optimal', 'robust'
        ]
        
        technical_keywords = [
            'neural', 'transformer', 'attention', 'learning', 'algorithm',
            'optimization', 'architecture', 'model', 'method', 'approach'
        ]
        
        # Score based on keyword presence
        quality_count = sum(1 for kw in high_quality_keywords if kw in text)
        technical_count = sum(1 for kw in technical_keywords if kw in text)
        
        score += min(quality_count * 2.0, 8.0)  # Up to 8 points for quality
        score += min(technical_count * 1.0, 6.0)  # Up to 6 points for technical content
        
        # Recency bonus
        try:
            if hasattr(paper['published'], 'replace'):
                # DateTime object
                paper_date = paper['published'].replace(tzinfo=None)
            else:
                # String or other format - try to parse
                paper_date = parser.parse(str(paper['published'])).replace(tzinfo=None)
            
            days_old = (datetime.now() - paper_date).days
            if days_old <= 7:
                score += 3.0
            elif days_old <= 30:
                score += 1.0
        except Exception as e:
            logger.error(f"Error in fallback recency calculation: {e}")
            score += 2.0  # Default bonus if date parsing fails
        
        # Length indicators
        if 50 <= len(paper['summary'].split()) <= 300:
            score += 2.0
        
        return min(score, 20.0)
    
    def score_papers(self, papers: List[Dict]) -> List[Dict]:
        """Score papers with rate limiting and batch processing."""
        if self.client is None:
            logger.warning("API client not available, using fallback for all papers")
            return super().score_papers(papers)
        
        logger.info(f"Starting API-based scoring of {len(papers)} papers using {self.provider}")
        
        for i, paper in enumerate(papers):
            try:
                paper['score'] = self.score_paper(paper)
                paper['score'] = round(paper['score'], 2)
                
                # Rate limiting: small delay between requests
                if i < len(papers) - 1:  # Don't sleep after the last paper
                    time.sleep(1)  # 1 second delay between requests
                    
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(papers)} papers")
                    
            except Exception as e:
                logger.error(f"Error scoring paper {i+1}: {e}")
                paper['score'] = self._fallback_scoring(paper)
        
        # Sort by score (descending)
        papers.sort(key=lambda x: x['score'], reverse=True)
        
        top_score = papers[0]['score'] if papers else 0
        logger.info(f"API scoring complete. Top score: {top_score:.2f}")
        
        return papers 