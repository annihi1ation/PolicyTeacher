#!/usr/bin/env python3
"""
Example usage of the CLI Teaching Agent

This script demonstrates different ways to use the teaching agent.
"""

import os
from teaching_agent_core import SimpleTeachingAgent
from models import EmotionState, LanguageLevel, StudentProfile
from utils import SessionStorage
from emotion_detector import EmotionDetector

def example_basic_usage():
    """Basic usage example"""
    print("=== Basic Usage Example ===\n")
    
    # Get API key from environment or use a placeholder
    api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
    
    # Create a simple teaching agent
    agent = SimpleTeachingAgent(
        session_id="example-session-001",
        api_key=api_key,
        model_name="gpt-3.5-turbo"
    )
    
    # Simulate a conversation
    messages = [
        "Hi! I'm excited to learn Chinese!",
        "What's the word for cat?",
        "猫! I know this one!",
        "I'm feeling a bit tired now..."
    ]
    
    print("Starting conversation...\n")
    
    for message in messages:
        print(f"Student: {message}")
        response = agent.chat(message)
        print(f"Xiao Lin: {response}\n")
    
    # Get session summary
    summary = agent.get_summary()
    print("\nSession Summary:")
    print(f"- Duration: {summary['duration_minutes']:.1f} minutes")
    print(f"- Messages: {summary['messages_count']}")
    print(f"- Current Level: {summary['current_level']}")
    print(f"- Words Learned: {summary['words_learned']}")
    
    # End session
    farewell = agent.end()
    print(f"\nXiao Lin: {farewell}")


def example_emotion_detection():
    """Example of emotion detection utility"""
    print("\n=== Emotion Detection Example ===\n")
    
    detector = EmotionDetector()
    
    test_messages = [
        "This is so cool! I love learning Chinese!",
        "I'm confused... this is hard",
        "I feel happy today",
        "I'm so tired, can we stop?",
        "I miss my mom..."
    ]
    
    for message in test_messages:
        emotion = detector.detect_emotion(message)
        print(f"Message: '{message}'")
        print(f"Detected emotion: {emotion.value}\n")


def example_profile_management():
    """Example of profile storage and retrieval"""
    print("\n=== Profile Management Example ===\n")
    
    storage = SessionStorage()
    
    # Create a test profile
    profile = StudentProfile(session_id="test-student-001")
    profile.language_level = LanguageLevel.L2
    profile.add_learned_word("猫", 50)
    profile.add_learned_word("狗", 30)
    profile.add_learned_word("水", 80)
    
    # Save profile
    storage.save_profile(profile)
    print("Profile saved!")
    
    # Load profile
    loaded_profile = storage.load_profile("test-student-001")
    if loaded_profile:
        print(f"Profile loaded: {loaded_profile.session_id}")
        print(f"Language level: {loaded_profile.language_level.value}")
        print(f"Learned words: {len(loaded_profile.learned_words)}")
        for word, mastery in loaded_profile.learned_words.items():
            print(f"  - {word}: {mastery}% mastery")


def example_with_custom_settings():
    """Example with custom API settings"""
    print("\n=== Custom Settings Example ===\n")
    
    # Custom settings for different providers
    agent = SimpleTeachingAgent(
        session_id="custom-session-001",
        api_key="your-openai-api-key-here",  # Replace with your actual API key
        base_url="https://api.openai.com/v1",  # or your custom endpoint
        model_name="gpt-4"  # or any compatible model
    )
    
    # Quick test
    response = agent.chat("Hello! 你好!")
    print(f"Response: {response}")
    
    agent.end()


if __name__ == "__main__":
    print("Chinese Teaching Agent - Usage Examples\n")
    print("Note: Make sure to set OPENAI_API_KEY environment variable\n")
    
    try:
        # Run examples
        example_basic_usage()
        example_emotion_detection()
        example_profile_management()
        
        # Uncomment to test with custom settings
        # example_with_custom_settings()
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        print("Make sure you have set up your API key correctly!")
