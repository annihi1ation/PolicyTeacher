"""
ReAct Teaching Agent - CLI version of the Chinese teaching agent
"""

from .teaching_agent_core import SimpleTeachingAgent, TeachingAgentCore
from .models import (
    LanguageLevel, EmotionState, EmotionTrend,
    ChatMessage, StudentProfile, TeachingContext,
    WordKnowledge, TeachingPolicy
)
from .utils import (
    WordManager, SessionStorage, get_encouragement,
    format_time_duration
)
from .emotion_detector import EmotionDetector
from .language_level_agent import LanguageLevelAgent
from .policy_generator_agent import PolicyGeneratorAgent

__version__ = "1.0.0"
__author__ = "Teaching Agent Team"

__all__ = [
    "SimpleTeachingAgent",
    "TeachingAgentCore",
    "LanguageLevel",
    "EmotionState",
    "EmotionTrend",
    "ChatMessage",
    "StudentProfile",
    "TeachingContext",
    "WordKnowledge",
    "TeachingPolicy",
    "EmotionDetector",
    "LanguageLevelAgent",
    "WordManager",
    "PolicyGeneratorAgent",
    "SessionStorage",
    "get_encouragement",
    "format_time_duration"
]
