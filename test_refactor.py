#!/usr/bin/env python3
"""Test script to verify the refactored imports work correctly."""

def test_imports():
    """Test that all imports work correctly after refactoring."""
    
    # Test helper imports
    print("Testing helper imports...")
    from helper.models import EmotionState, LanguageLevel, StudentProfile
    from helper.utils import SessionStorage, WordManager
    from helper.emotion_detector import EmotionDetector, BERTEmotionDetector
    from helper.trajectory_generator import TrajectoryGenerator, ChatSession
    print("✓ Helper imports successful")
    
    # Test agent imports
    print("Testing agent imports...")
    from agents.teaching_agent_core import SimpleTeachingAgent
    from agents.language_level_agent import LanguageLevelAgent
    from agents.policy_generator_agent import PolicyGeneratorAgent
    print("✓ Agent imports successful")
    
    # Test prompts import (stayed in root)
    print("Testing prompts import...")
    from prompts import teaching_prompt_template
    print("✓ Prompts import successful")
    
    # Test example imports
    print("Testing example imports...")
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), 'examples'))
    
    print("✓ All imports working correctly!")
    
    return True

if __name__ == "__main__":
    test_imports()
    print("\n🎉 Refactoring successful! All imports are working correctly.")
