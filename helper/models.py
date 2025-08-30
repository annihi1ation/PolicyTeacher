"""Data models for the CLI teaching agent"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum


class LanguageLevel(Enum):
    """Language proficiency levels"""
    L1 = "L1"  # Emerging Awareness
    L2 = "L2"  # Basic Expression
    L3 = "L3"  # Sentence Development
    L4 = "L4"  # Interactive Communication
    L5 = "L5"  # Structured & Logical Speech


class EmotionState(Enum):
    """Student emotion states"""
    EXCITED = "excited"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    TIRED = "tired"
    SAD = "sad"


class EmotionTrend(Enum):
    """Emotion trend directions"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


@dataclass
class ChatMessage:
    """Single chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    emotion_detected: Optional[EmotionState] = None
    chinese_words_used: List[str] = field(default_factory=list)


@dataclass
class StudentProfile:
    """Student profile and progress tracking"""
    session_id: str
    language_level: LanguageLevel = LanguageLevel.L1
    emotion_history: List[EmotionState] = field(default_factory=list)
    learned_words: Dict[str, int] = field(default_factory=dict)  # word -> mastery level (0-100)
    session_count: int = 0
    total_interaction_time: float = 0.0  # in minutes
    preferred_topics: List[str] = field(default_factory=list)
    
    def add_learned_word(self, word: str, increment: int = 10):
        """Track word learning progress"""
        if word in self.learned_words:
            self.learned_words[word] = min(100, self.learned_words[word] + increment)
        else:
            self.learned_words[word] = increment
    
    def get_mastery_level(self, word: str) -> int:
        """Get mastery level for a specific word"""
        return self.learned_words.get(word, 0)


@dataclass
class TeachingContext:
    """Current teaching session context"""
    student_profile: StudentProfile
    current_emotion: EmotionState = EmotionState.NEUTRAL
    emotion_trend: EmotionTrend = EmotionTrend.STABLE
    needs_intervention: bool = False
    current_word_category: str = "animals"
    session_messages: List[ChatMessage] = field(default_factory=list)
    session_start_time: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, emotion: Optional[EmotionState] = None):
        """Add a message to the session"""
        msg = ChatMessage(role=role, content=content, emotion_detected=emotion)
        self.session_messages.append(msg)
        
        # Update emotion history if emotion is detected
        if emotion and role == "user":
            self.student_profile.emotion_history.append(emotion)
            self._update_emotion_trend()
    
    def _update_emotion_trend(self):
        """Update emotion trend based on recent history"""
        if len(self.student_profile.emotion_history) < 3:
            return
        
        recent_emotions = self.student_profile.emotion_history[-5:]
        
        # Simple trend detection based on emotion values
        emotion_values = {
            EmotionState.EXCITED: 5,
            EmotionState.HAPPY: 4,
            EmotionState.NEUTRAL: 3,
            EmotionState.FRUSTRATED: 2,
            EmotionState.TIRED: 1,
            EmotionState.SAD: 0
        }
        
        values = [emotion_values[e] for e in recent_emotions]
        
        # Calculate trend
        if len(values) >= 3:
            recent_avg = sum(values[-3:]) / 3
            older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else values[0]
            
            if recent_avg > older_avg + 0.5:
                self.emotion_trend = EmotionTrend.IMPROVING
            elif recent_avg < older_avg - 0.5:
                self.emotion_trend = EmotionTrend.DECLINING
            else:
                self.emotion_trend = EmotionTrend.STABLE
        
        # Check if intervention is needed
        self.needs_intervention = (
            self.current_emotion in [EmotionState.FRUSTRATED, EmotionState.SAD, EmotionState.TIRED] or
            self.emotion_trend == EmotionTrend.DECLINING
        )
    
    def get_session_duration(self) -> float:
        """Get current session duration in minutes"""
        return (datetime.now() - self.session_start_time).total_seconds() / 60


@dataclass
class WordKnowledge:
    """Chinese word knowledge entry"""
    chinese: str
    pinyin: str
    english: str
    category: str
    difficulty_level: LanguageLevel
    usage_examples: List[str] = field(default_factory=list)
    emoji: Optional[str] = None


@dataclass
class TeachingPolicy:
    """Dynamic teaching policy"""
    policy_text: str
    timestamp: datetime = field(default_factory=datetime.now)
    context_summary: Dict[str, str] = field(default_factory=dict)
    effectiveness_score: Optional[float] = None  # 0-1, set after evaluation
