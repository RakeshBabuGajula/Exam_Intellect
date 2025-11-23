"""
Integrations Module

This module handles external API integrations for the ExamIntellect system:
- Gemini LLM for AI analysis and feedback generation
- Google API for fact-checking and verification
- OpenAI for content generation and analysis
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logging.warning("python-dotenv not installed. Environment variables must be set manually.")

# Third-party imports (would be installed via requirements.txt)
try:
    import google.generativeai as genai
    import openai
    import requests
except ImportError as e:
    logging.warning(f"Missing dependencies: {e}. Install with: pip install -r requirements.txt")

logger = logging.getLogger(__name__)

def truncate_prompt(prompt: str, max_chars: int = 10000) -> str:
    """
    Truncate prompt to prevent 413 Request Entity Too Large errors.

    Args:
        prompt: The input prompt
        max_chars: Maximum character limit (default 10000, roughly 2500 tokens)

    Returns:
        str: Truncated prompt with warning if truncated
    """
    if len(prompt) <= max_chars:
        return prompt

    truncated = prompt[:max_chars]
    logger.warning(f"Prompt truncated from {len(prompt)} to {max_chars} characters to prevent 413 error")
    return truncated + "\n\n[Note: Prompt was truncated due to length limits]"

class IntegrationManager:
    """
    Manages all external API integrations for EduGuard.

    This class handles initialization and configuration of external API clients
    including Gemini LLM, OpenAI, and Google APIs.
    """

    def __init__(self):
        """
        Initialize the integration manager with API keys from environment variables.

        Loads API keys from environment and initializes available clients.
        """
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.google_api_key = os.getenv('GOOGLE_API_KEY')

        # Initialize clients if keys are available
        self._initialize_clients()

    def _initialize_clients(self):
        """
        Initialize API clients based on available API keys.

        Attempts to configure Gemini, OpenAI, and Google API clients.
        Logs warnings for any failed initializations.
        """
        if self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                logger.info("Gemini LLM client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")

        if self.openai_api_key:
            try:
                openai.api_key = self.openai_api_key
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")

def initialize_integrations() -> IntegrationManager:
    """
    Initialize and return the integration manager.

    Returns:
        IntegrationManager: Configured integration manager instance
    """
    return IntegrationManager()

def call_gemini_llm(prompt: str, max_tokens: int = 1000) -> str:
    """
    Call Gemini LLM for text generation and analysis.

    Args:
        prompt: The input prompt for the LLM
        max_tokens: Maximum tokens to generate

    Returns:
        str: Generated response from Gemini
    """
    try:
        # Check payload size to prevent 413 errors (50MB limit for safety)
        payload_size = len(prompt.encode('utf-8'))
        if payload_size > 50 * 1024 * 1024:
            return "Error: Prompt too large for API limits (max 50MB)"

        manager = IntegrationManager()
        if not hasattr(manager, 'gemini_model'):
            return "Gemini LLM not available. Please check API key configuration."

        response = manager.gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7
            )
        )
        return response.text.strip()

    except Exception as e:
        logger.error(f"Gemini LLM call failed: {e}")
        return f"Error calling Gemini LLM: {str(e)}"

def call_openai_api(prompt: str, model: str = "gpt-3.5-turbo",
                   max_tokens: int = 1000) -> str:
    """
    Call OpenAI API for text generation and analysis.

    Args:
        prompt: The input prompt for OpenAI
        model: OpenAI model to use
        max_tokens: Maximum tokens to generate

    Returns:
        str: Generated response from OpenAI
    """
    try:
        # Truncate prompt to prevent 413 errors
        truncated_prompt = truncate_prompt(prompt)

        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": truncated_prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error(f"OpenAI API call failed: {e}")
        return f"Error calling OpenAI API: {str(e)}"

def fact_check_with_openai(statement: str) -> Dict[str, Any]:
    """
    Use OpenAI to fact-check a statement.

    Args:
        statement: The statement to fact-check

    Returns:
        Dict: Fact-checking results with verdict and explanation
    """
    try:
        prompt = f"""
        Please fact-check the following statement. Provide:
        1. A verdict (True, False, or Partially True)
        2. A brief explanation of your reasoning
        3. Confidence level (High, Medium, Low)

        Statement: {statement}

        Format your response as JSON with keys: verdict, explanation, confidence
        """

        response = call_openai_api(prompt, max_tokens=500)

        # Attempt to parse JSON response
        try:
            import json
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # Fallback: extract information manually
            return {
                'verdict': 'Unknown',
                'explanation': response,
                'confidence': 'Low'
            }

    except Exception as e:
        logger.error(f"Fact-checking failed: {e}")
        return {
            'verdict': 'Error',
            'explanation': f'Fact-checking service unavailable: {str(e)}',
            'confidence': 'None'
        }

def search_google_facts(query: str) -> Dict[str, Any]:
    """
    Search Google for fact-checking information.

    Args:
        query: Search query for fact-checking

    Returns:
        Dict: Search results and fact-checking data
    """
    try:
        manager = IntegrationManager()
        if not manager.google_api_key:
            return {"error": "Google API key not configured"}

        # Google Custom Search API (placeholder implementation)
        search_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': manager.google_api_key,
            'cx': os.getenv('GOOGLE_SEARCH_ENGINE_ID', ''),  # Would need to be set
            'q': query,
            'num': 5
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()

        results = response.json()

        # Process search results for fact-checking
        facts = []
        if 'items' in results:
            for item in results['items']:
                facts.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'source': item.get('displayLink', '')
                })

        return {
            'query': query,
            'facts_found': len(facts),
            'sources': facts,
            'timestamp': str(datetime.now())
        }

    except Exception as e:
        logger.error(f"Google search failed: {e}")
        return {"error": f"Google search failed: {str(e)}"}

def analyze_behavior_with_gemini(video_description: str,
                                audio_transcript: str = "") -> Dict[str, Any]:
    """
    Use Gemini to analyze behavioral patterns from video/audio data.

    Args:
        video_description: Description of video behavior
        audio_transcript: Audio transcript if available

    Returns:
        Dict: Analysis results including suspicious indicators
    """
    try:
        # Truncate inputs to prevent 413 errors
        truncated_video = truncate_prompt(video_description, max_chars=5000)
        truncated_audio = truncate_prompt(audio_transcript, max_chars=5000)

        prompt = f"""
        Analyze the following exam session behavior for potential irregularities:

        Video Description: {truncated_video}
        Audio Transcript: {truncated_audio}

        Please identify:
        1. Suspicious behaviors or patterns
        2. Risk level (Low, Medium, High, Critical)
        3. Specific concerns or red flags
        4. Recommendations for further action

        Format your response as JSON with keys: suspicious_behaviors, risk_level, concerns, recommendations
        """

        response = call_gemini_llm(prompt, max_tokens=800)

        # Attempt to parse JSON
        try:
            import json
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                'suspicious_behaviors': [],
                'risk_level': 'Unknown',
                'concerns': [response],
                'recommendations': ['Manual review recommended']
            }

    except Exception as e:
        logger.error(f"Behavior analysis failed: {e}")
        return {
            'error': str(e),
            'suspicious_behaviors': [],
            'risk_level': 'Error',
            'concerns': ['Analysis service unavailable'],
            'recommendations': ['Contact technical support']
        }

def generate_feedback_with_ai(student_performance: Dict,
                             session_data: Dict) -> str:
    """
    Generate personalized feedback using AI.

    Args:
        student_performance: Student performance metrics
        session_data: Session behavior data

    Returns:
        str: Personalized feedback message
    """
    try:
        prompt = f"""
        Generate constructive, encouraging feedback for a student based on their exam performance and session behavior.

        Performance Data:
        - Score: {student_performance.get('score', 'N/A')}%
        - Weak Areas: {', '.join(student_performance.get('weak_areas', []))}
        - Completion Time: {student_performance.get('duration', 'N/A')} minutes

        Session Behavior:
        - Alerts: {session_data.get('alerts_count', 0)}
        - Suspicious Activities: {session_data.get('suspicious_count', 0)}
        - Risk Level: {session_data.get('risk_level', 'low')}

        Provide feedback that:
        1. Acknowledges strengths and improvements
        2. Addresses areas for growth
        3. Offers specific, actionable recommendations
        4. Maintains a positive, supportive tone
        5. Considers both academic performance and exam integrity
        """

        return call_gemini_llm(prompt, max_tokens=600)

    except Exception as e:
        logger.error(f"Feedback generation failed: {e}")
        return "Personalized feedback is currently unavailable. Please contact your instructor for guidance."
