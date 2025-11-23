"""
ExamIntellect Core Package

This package contains the core components of the ExamIntellect AI proctoring system.
"""

from .session_manager import SessionManager
from .integrations import IntegrationManager, call_gemini_llm, analyze_behavior_with_gemini
from .agents import ProctorAgent, TutorAgent, CommunicationAgent

__all__ = [
    'SessionManager',
    'IntegrationManager',
    'call_gemini_llm',
    'analyze_behavior_with_gemini',
    'ProctorAgent',
    'TutorAgent',
    'CommunicationAgent'
]
