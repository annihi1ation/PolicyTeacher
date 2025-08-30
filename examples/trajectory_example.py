"""Example usage of the trajectory generator"""

import os
from datetime import datetime
from helper.trajectory_generator import TrajectoryGenerator, ChatSession, TrajectoryStep
from helper.models import ChatMessage, EmotionState, LanguageLevel
from helper.emotion_detector import BERTEmotionDetector
from agents.policy_generator_agent import PolicyGeneratorAgent


def create_sample_chat_session() -> ChatSession:
    """Create a sample chat session for demonstration"""
    messages = [
        ChatMessage(
            role="user",
            content="Hi! I want to learn Chinese!",
            timestamp=datetime(2025, 8, 29, 10, 0, 0),
            emotion_detected=EmotionState.EXCITED
        ),
        ChatMessage(
            role="assistant",
            content="That's wonderful! Let's start with some basic words. How are you feeling?",
            timestamp=datetime(2025, 8, 29, 10, 0, 30)
        ),
        ChatMessage(
            role="user",
            content="I'm excited but a little nervous",
            timestamp=datetime(2025, 8, 29, 10, 1, 0),
            emotion_detected=EmotionState.HAPPY
        ),
        ChatMessage(
            role="assistant",
            content="That's completely normal! Let's learn the word for 'cat' - 猫 (māo)",
            timestamp=datetime(2025, 8, 29, 10, 1, 30)
        ),
        ChatMessage(
            role="user",
            content="Mao... that's hard to pronounce",
            timestamp=datetime(2025, 8, 29, 10, 2, 0),
            emotion_detected=EmotionState.FRUSTRATED
        ),
        ChatMessage(
            role="assistant",
            content="Don't worry! Let's practice together slowly. MAO... like 'meow' but with 'ah' sound",
            timestamp=datetime(2025, 8, 29, 10, 2, 30)
        ),
        ChatMessage(
            role="user",
            content="Oh I think I got it! Mao!",
            timestamp=datetime(2025, 8, 29, 10, 3, 0),
            emotion_detected=EmotionState.HAPPY
        ),
        ChatMessage(
            role="user",
            content="What about dog?",
            timestamp=datetime(2025, 8, 29, 10, 3, 30),
            emotion_detected=EmotionState.EXCITED
        )
    ]
    
    return ChatSession(
        session_id="demo_session_001",
        messages=messages,
        start_time=datetime(2025, 8, 29, 10, 0, 0),
        end_time=datetime(2025, 8, 29, 10, 4, 0),
        student_language_level=LanguageLevel.L1
    )


def example_basic_trajectory_generation():
    """Example 1: Basic trajectory generation without real models"""
    print("=== Example 1: Basic Trajectory Generation ===")
    
    # Create trajectory generator without models (will use fallbacks)
    generator = TrajectoryGenerator()
    
    # Create sample session
    session = create_sample_chat_session()
    
    # Generate trajectory
    trajectory = generator.generate_trajectory(session)
    
    print(f"Generated trajectory with {len(trajectory)} steps:")
    for i, step in enumerate(trajectory):
        print(f"\nStep {i+1}:")
        print(f"  State (S): {step.state}")
        print(f"  Action (A): {step.action}")
        print(f"  Reward (R): {step.reward.value}")
        print(f"  Timestamp: {step.timestamp}")
    
    # Save trajectory
    output_path = "sample_trajectory.json"
    generator.save_trajectory(trajectory, output_path)
    print(f"\nTrajectory saved to {output_path}")
    
    # Get statistics
    stats = generator.get_trajectory_statistics(trajectory)
    print(f"\nTrajectory Statistics:")
    print(f"  Total steps: {stats['total_steps']}")
    print(f"  Positive emotion ratio: {stats['positive_emotion_ratio']:.2f}")
    print(f"  Session duration: {stats['session_duration_minutes']:.1f} minutes")
    print(f"  Emotion distribution: {stats['emotion_distribution']}")


def example_with_real_models():
    """Example 2: Using real emotion detector and policy generator"""
    print("\n=== Example 2: With Real Models ===")
    
    # Initialize models (you would need actual API keys)
    try:
        emotion_detector = BERTEmotionDetector()
        print("✓ Emotion detector loaded")
    except Exception as e:
        print(f"✗ Could not load emotion detector: {e}")
        emotion_detector = None
    
    try:
        # You would need to provide actual API key and base URL
        policy_generator = PolicyGeneratorAgent(
            api_key="your-api-key-here",
            base_url="your-base-url-here"
        )
        print("✓ Policy generator loaded")
    except Exception as e:
        print(f"✗ Could not load policy generator: {e}")
        policy_generator = None
    
    # Create trajectory generator with models
    generator = TrajectoryGenerator(
        emotion_detector=emotion_detector,
        policy_generator=policy_generator
    )
    
    # Create session without pre-detected emotions (let the detector work)
    session = create_sample_chat_session()
    # Remove pre-detected emotions to test real detection
    for msg in session.messages:
        if msg.role == "user":
            msg.emotion_detected = None
    
    # Generate trajectory
    trajectory = generator.generate_trajectory(session)
    
    print(f"Generated trajectory with {len(trajectory)} steps using real models")
    
    # Show first few steps
    for i, step in enumerate(trajectory[:3]):
        print(f"\nStep {i+1}:")
        print(f"  State: {step.state[:50]}...")
        print(f"  Reward: {step.reward.value}")
        print(f"  Action: {step.action[:100]}...")


def example_from_log_file():
    """Example 3: Generate trajectory from log file"""
    print("\n=== Example 3: From Log File ===")
    
    # Create a sample log file
    log_content = """2025-08-29T10:00:00 [user] Hello! I want to learn Chinese
2025-08-29T10:00:30 [assistant] Great! Let's start with basic greetings
2025-08-29T10:01:00 [user] How do I say hello?
2025-08-29T10:01:30 [assistant] In Chinese, hello is 你好 (nǐ hǎo)
2025-08-29T10:02:00 [user] Ni hao! That's fun!
2025-08-29T10:02:30 [assistant] Excellent pronunciation! Let's learn more
2025-08-29T10:03:00 [user] This is getting hard...
2025-08-29T10:03:30 [assistant] No worries, let's take it slow"""
    
    log_file_path = "sample_session.log"
    with open(log_file_path, 'w', encoding='utf-8') as f:
        f.write(log_content)
    
    # Generate trajectory from log
    generator = TrajectoryGenerator()
    trajectory = generator.generate_trajectory_from_log(log_file_path)
    
    print(f"Generated trajectory from log file with {len(trajectory)} steps")
    
    # Clean up
    if os.path.exists(log_file_path):
        os.remove(log_file_path)


def example_load_and_analyze():
    """Example 4: Load saved trajectory and analyze"""
    print("\n=== Example 4: Load and Analyze Trajectory ===")
    
    trajectory_path = "sample_trajectory.json"
    
    if os.path.exists(trajectory_path):
        generator = TrajectoryGenerator()
        trajectory = generator.load_trajectory(trajectory_path)
        
        print(f"Loaded trajectory with {len(trajectory)} steps")
        
        # Analyze trajectory
        stats = generator.get_trajectory_statistics(trajectory)
        
        print("\nDetailed Analysis:")
        print(f"  Session Duration: {stats['session_duration_minutes']:.1f} minutes")
        print(f"  Total Interactions: {stats['total_steps']}")
        print(f"  Positive Emotion Ratio: {stats['positive_emotion_ratio']:.1%}")
        
        print("\nEmotion Distribution:")
        for emotion, ratio in stats['emotion_distribution'].items():
            if ratio > 0:
                print(f"  {emotion}: {ratio:.1%}")
        
        # Clean up
        os.remove(trajectory_path)
    else:
        print("No saved trajectory found. Run example 1 first.")


if __name__ == "__main__":
    print("Trajectory Generator Examples")
    print("=" * 40)
    
    # Run examples
    example_basic_trajectory_generation()
    example_with_real_models()
    example_from_log_file()
    example_load_and_analyze()
    
    print("\n" + "=" * 40)
    print("All examples completed!")
