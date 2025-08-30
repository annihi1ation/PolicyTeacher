"""Utility functions for the CLI teaching agent"""

import os
import json
import random
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

from helper.models import (
    EmotionState, LanguageLevel, StudentProfile, 
    WordKnowledge, TeachingPolicy, ChatMessage
)




class WordManager:
    """Manage Chinese word knowledge base"""
    
    def __init__(self, word_data_path: Optional[str] = None):
        self.word_data_path = word_data_path or "src/data/word_knowledge_base.json"
        self.words = self._load_words()
        self.categories = self._organize_by_category()
    
    def _load_words(self) -> List[WordKnowledge]:
        """Load words from JSON file"""
        if not os.path.exists(self.word_data_path):
            # Return default words if file doesn't exist
            return self._get_default_words()
        
        try:
            with open(self.word_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [
                    WordKnowledge(
                        chinese=w["chinese"],
                        pinyin=w["pinyin"],
                        english=w["english"],
                        category=w["category"],
                        difficulty_level=LanguageLevel[w.get("level", "L1")],
                        usage_examples=w.get("examples", []),
                        emoji=w.get("emoji")
                    )
                    for w in data.get("words", [])
                ]
        except Exception as e:
            print(f"Error loading words: {e}")
            return self._get_default_words()
    
    def _get_default_words(self) -> List[WordKnowledge]:
        """Get default word set"""
        return [
            # Animals
            WordKnowledge("猫", "māo", "cat", "animals", LanguageLevel.L1, ["我有一只猫。"], "🐱"),
            WordKnowledge("狗", "gǒu", "dog", "animals", LanguageLevel.L1, ["小狗很可爱。"], "🐶"),
            WordKnowledge("鸟", "niǎo", "bird", "animals", LanguageLevel.L1, ["鸟在飞。"], "🐦"),
            
            # Food
            WordKnowledge("水", "shuǐ", "water", "food", LanguageLevel.L1, ["我要喝水。"], "💧"),
            WordKnowledge("苹果", "píngguǒ", "apple", "food", LanguageLevel.L1, ["红苹果很甜。"], "🍎"),
            WordKnowledge("面包", "miànbāo", "bread", "food", LanguageLevel.L2, ["我喜欢吃面包。"], "🍞"),
            
            # Family
            WordKnowledge("妈妈", "māma", "mom", "family", LanguageLevel.L1, ["我爱妈妈。"], "👩"),
            WordKnowledge("爸爸", "bàba", "dad", "family", LanguageLevel.L1, ["爸爸很高。"], "👨"),
            
            # Actions
            WordKnowledge("吃", "chī", "eat", "actions", LanguageLevel.L1, ["我要吃饭。"], "🍽️"),
            WordKnowledge("喝", "hē", "drink", "actions", LanguageLevel.L1, ["喝水很重要。"], "🥤"),
            WordKnowledge("玩", "wán", "play", "actions", LanguageLevel.L1, ["我们一起玩。"], "🎮"),
        ]
    
    def _organize_by_category(self) -> Dict[str, List[WordKnowledge]]:
        """Organize words by category"""
        categories = {}
        for word in self.words:
            if word.category not in categories:
                categories[word.category] = []
            categories[word.category].append(word)
        return categories
    
    def get_random_category(self) -> str:
        """Get a random category"""
        return random.choice(list(self.categories.keys()))
    
    def get_word_for_level(self, level: LanguageLevel, category: Optional[str] = None) -> Optional[WordKnowledge]:
        """Get a random word appropriate for the given level"""
        # Filter words by level
        appropriate_words = [w for w in self.words if w.difficulty_level.value <= level.value]
        
        # Filter by category if specified
        if category and category in self.categories:
            appropriate_words = [w for w in appropriate_words if w.category == category]
        
        return random.choice(appropriate_words) if appropriate_words else None




class SessionStorage:
    """Simple file-based session storage"""
    
    def __init__(self, data_dir: str = "src/ReAct/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def save_profile(self, profile: StudentProfile):
        """Save student profile to file"""
        profile_path = self.data_dir / f"{profile.session_id}_profile.json"
        
        data = {
            "session_id": profile.session_id,
            "language_level": profile.language_level.value,
            "emotion_history": [e.value for e in profile.emotion_history[-50:]],  # Keep last 50
            "learned_words": profile.learned_words,
            "session_count": profile.session_count,
            "total_interaction_time": profile.total_interaction_time,
            "preferred_topics": profile.preferred_topics
        }
        
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_profile(self, session_id: str) -> Optional[StudentProfile]:
        """Load student profile from file"""
        profile_path = self.data_dir / f"{session_id}_profile.json"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = StudentProfile(session_id=session_id)
            profile.language_level = LanguageLevel[data.get("language_level", "L1")]
            profile.emotion_history = [EmotionState(e) for e in data.get("emotion_history", [])]
            profile.learned_words = data.get("learned_words", {})
            profile.session_count = data.get("session_count", 0)
            profile.total_interaction_time = data.get("total_interaction_time", 0.0)
            profile.preferred_topics = data.get("preferred_topics", [])
            
            return profile
        except Exception as e:
            print(f"Error loading profile: {e}")
            return None
    
    def save_session_log(self, session_id: str, messages: List[ChatMessage]):
        """Save session messages to log file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = self.data_dir / f"{session_id}_session_{timestamp}.log"
        
        with open(log_path, 'w', encoding='utf-8') as f:
            for msg in messages:
                f.write(f"[{msg.timestamp.strftime('%H:%M:%S')}] {msg.role}: {msg.content}\n")
                if msg.emotion_detected:
                    f.write(f"  [Emotion: {msg.emotion_detected.value}]\n")
                if msg.chinese_words_used:
                    f.write(f"  [Chinese words: {', '.join(msg.chinese_words_used)}]\n")
                f.write("\n")


def format_time_duration(minutes: float) -> str:
    """Format duration in a kid-friendly way"""
    if minutes < 1:
        return "just started"
    elif minutes < 5:
        return "a few minutes"
    elif minutes < 10:
        return "a little while"
    elif minutes < 30:
        return f"about {int(minutes)} minutes"
    else:
        return "a long time"


def get_encouragement() -> str:
    """Get a random encouragement phrase"""
    phrases = [
        "You're doing great! 🌟",
        "Awesome job! 🎉",
        "Keep it up! 💪",
        "You're amazing! ✨",
        "Way to go! 🚀",
        "Super cool! 😎",
        "You rock! 🎸",
        "Fantastic! 🌈"
    ]
    return random.choice(phrases)
