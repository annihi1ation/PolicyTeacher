"""Trajectory generator for chat sessions"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
import json
import logging

from helper.models import EmotionState, LanguageLevel, EmotionTrend, ChatMessage, TeachingContext
from helper.emotion_detector import BERTEmotionDetector
from agents.policy_generator_agent import PolicyGeneratorAgent


@dataclass
class TrajectoryStep:
    """Single step in a trajectory: (State, Action, Reward)"""
    state: str  # User input (S)
    action: str  # Policy agent plan (A)
    reward: EmotionState  # User's emotion (R)
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ChatSession:
    """Chat session data structure"""
    session_id: str
    messages: List[ChatMessage]
    start_time: datetime
    end_time: Optional[datetime] = None
    student_language_level: LanguageLevel = LanguageLevel.L1
    session_metadata: Optional[Dict[str, Any]] = None


class TrajectoryGenerator:
    """Generates (S, A, R) trajectories from chat sessions"""
    
    def __init__(self, 
                 emotion_detector: Optional[BERTEmotionDetector] = None,
                 policy_generator: Optional[PolicyGeneratorAgent] = None):
        """
        Initialize trajectory generator
        
        Args:
            emotion_detector: Emotion detection model (optional for replay)
            policy_generator: Policy generation agent (optional for replay)
        """
        self.emotion_detector = emotion_detector
        self.policy_generator = policy_generator
        self.logger = logging.getLogger(__name__)
    
    def generate_trajectory(self, chat_session: ChatSession) -> List[TrajectoryStep]:
        """
        Generate trajectory from a chat session
        
        Args:
            chat_session: Chat session with messages
            
        Returns:
            List of TrajectoryStep objects representing (S, A, R) sequence
        """
        trajectory = []
        current_level = chat_session.student_language_level
        emotion_history = []
        
        # Process messages in sequence
        user_messages = [msg for msg in chat_session.messages if msg.role == "user"]
        
        for i, user_msg in enumerate(user_messages):
            try:
                # S: State (user input)
                state = user_msg.content
                
                # R: Reward (user's emotion)
                if user_msg.emotion_detected:
                    # Use pre-detected emotion if available
                    emotion = user_msg.emotion_detected
                else:
                    # Detect emotion if not available and detector is provided
                    if self.emotion_detector:
                        emotion = self.emotion_detector.detect_emotion(state)
                    else:
                        emotion = EmotionState.NEUTRAL  # Default fallback
                
                emotion_history.append(emotion)
                
                # Calculate emotion trend
                emotion_trend = self._calculate_emotion_trend(emotion_history)
                
                # A: Action (policy agent plan)
                if self.policy_generator:
                    # Generate policy in real-time
                    context = {
                        "session_progress": f"{i+1}/{len(user_messages)}",
                        "previous_emotions": str([e.value for e in emotion_history[-3:]])
                    }
                    action = self.policy_generator.generate_policy(
                        emotion=emotion,
                        level=current_level,
                        trend=emotion_trend,
                        context=context
                    )
                else:
                    # Use default policy if generator not available
                    action = self._generate_default_policy(emotion, current_level, emotion_trend)
                
                # Create trajectory step
                step = TrajectoryStep(
                    state=state,
                    action=action,
                    reward=emotion,
                    timestamp=user_msg.timestamp,
                    metadata={
                        "message_index": i,
                        "language_level": current_level.value,
                        "emotion_trend": emotion_trend.value,
                        "session_id": chat_session.session_id
                    }
                )
                
                trajectory.append(step)
                
                # Update language level based on progress (simple heuristic)
                if i > 0 and i % 5 == 0:  # Every 5 interactions, consider level update
                    current_level = self._update_language_level(emotion_history, current_level)
                
            except Exception as e:
                self.logger.error(f"Error processing message {i}: {e}")
                continue
        
        return trajectory
    
    def generate_trajectory_from_log(self, log_file_path: str) -> List[TrajectoryStep]:
        """
        Generate trajectory from a chat log file
        
        Args:
            log_file_path: Path to chat session log file
            
        Returns:
            List of TrajectoryStep objects
        """
        try:
            chat_session = self._parse_log_file(log_file_path)
            return self.generate_trajectory(chat_session)
        except Exception as e:
            self.logger.error(f"Error parsing log file {log_file_path}: {e}")
            return []
    
    def save_trajectory(self, trajectory: List[TrajectoryStep], output_path: str):
        """
        Save trajectory to file
        
        Args:
            trajectory: List of trajectory steps
            output_path: Output file path
        """
        try:
            trajectory_data = []
            for step in trajectory:
                step_data = {
                    "state": step.state,
                    "action": step.action,
                    "reward": step.reward.value,
                    "timestamp": step.timestamp.isoformat(),
                    "metadata": step.metadata
                }
                trajectory_data.append(step_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(trajectory_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Trajectory saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error saving trajectory: {e}")
    
    def load_trajectory(self, trajectory_path: str) -> List[TrajectoryStep]:
        """
        Load trajectory from file
        
        Args:
            trajectory_path: Path to trajectory file
            
        Returns:
            List of TrajectoryStep objects
        """
        try:
            with open(trajectory_path, 'r', encoding='utf-8') as f:
                trajectory_data = json.load(f)
            
            trajectory = []
            for step_data in trajectory_data:
                step = TrajectoryStep(
                    state=step_data["state"],
                    action=step_data["action"],
                    reward=EmotionState(step_data["reward"]),
                    timestamp=datetime.fromisoformat(step_data["timestamp"]),
                    metadata=step_data.get("metadata")
                )
                trajectory.append(step)
            
            return trajectory
            
        except Exception as e:
            self.logger.error(f"Error loading trajectory: {e}")
            return []
    
    def _calculate_emotion_trend(self, emotion_history: List[EmotionState]) -> EmotionTrend:
        """Calculate emotion trend from history"""
        if len(emotion_history) < 3:
            return EmotionTrend.STABLE
        
        # Emotion values for trend calculation
        emotion_values = {
            EmotionState.EXCITED: 5,
            EmotionState.HAPPY: 4,
            EmotionState.NEUTRAL: 3,
            EmotionState.FRUSTRATED: 2,
            EmotionState.TIRED: 1,
            EmotionState.SAD: 0
        }
        
        recent_emotions = emotion_history[-5:]  # Last 5 emotions
        values = [emotion_values[e] for e in recent_emotions]
        
        if len(values) >= 3:
            recent_avg = sum(values[-3:]) / 3
            older_avg = sum(values[:-3]) / len(values[:-3]) if len(values) > 3 else values[0]
            
            if recent_avg > older_avg + 0.5:
                return EmotionTrend.IMPROVING
            elif recent_avg < older_avg - 0.5:
                return EmotionTrend.DECLINING
            else:
                return EmotionTrend.STABLE
        
        return EmotionTrend.STABLE
    
    def _update_language_level(self, emotion_history: List[EmotionState], current_level: LanguageLevel) -> LanguageLevel:
        """Simple heuristic to update language level based on emotional progress"""
        if len(emotion_history) < 5:
            return current_level
        
        # Count positive emotions in recent history
        recent_emotions = emotion_history[-5:]
        positive_count = sum(1 for e in recent_emotions 
                           if e in [EmotionState.EXCITED, EmotionState.HAPPY])
        
        # Advance level if student is consistently happy/excited
        if positive_count >= 4 and current_level != LanguageLevel.L5:
            levels = list(LanguageLevel)
            current_index = levels.index(current_level)
            return levels[min(current_index + 1, len(levels) - 1)]
        
        return current_level
    
    def _generate_default_policy(self, emotion: EmotionState, level: LanguageLevel, trend: EmotionTrend) -> str:
        """Generate a simple default policy when policy generator is not available"""
        emotion_responses = {
            EmotionState.EXCITED: "Match their excitement with engaging activities!",
            EmotionState.HAPPY: "Keep the positive momentum with fun challenges.",
            EmotionState.NEUTRAL: "Spark interest with interactive content.",
            EmotionState.FRUSTRATED: "Provide support and easier content.",
            EmotionState.TIRED: "Use gentle, low-energy activities.",
            EmotionState.SAD: "Offer comfort and emotional support."
        }
        
        base_response = emotion_responses.get(emotion, "Adapt to student needs.")
        level_note = f" Focus on {level.value} level content."
        trend_note = f" Emotion trend: {trend.value}."
        
        return base_response + level_note + trend_note
    
    def _parse_log_file(self, log_file_path: str) -> ChatSession:
        """
        Parse a chat session log file
        
        Args:
            log_file_path: Path to log file
            
        Returns:
            ChatSession object
        """
        messages = []
        session_id = "unknown"
        start_time = datetime.now()
        
        try:
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract session ID from filename
            import os
            filename = os.path.basename(log_file_path)
            if '_session_' in filename:
                session_id = filename.split('_session_')[0]
            
            # Parse messages (simple format assumption)
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Expected format: "TIMESTAMP [ROLE] MESSAGE"
                if '[' in line and ']' in line:
                    try:
                        timestamp_str = line.split('[')[0].strip()
                        role_and_message = line.split('[')[1]
                        role = role_and_message.split(']')[0]
                        message = ']'.join(role_and_message.split(']')[1:]).strip()
                        
                        # Parse timestamp (simple format)
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except:
                            timestamp = datetime.now()
                        
                        if message:
                            chat_msg = ChatMessage(
                                role=role.lower(),
                                content=message,
                                timestamp=timestamp
                            )
                            messages.append(chat_msg)
                            
                            if not messages:  # First message sets start time
                                start_time = timestamp
                                
                    except Exception as e:
                        self.logger.warning(f"Skipping malformed log line: {line[:50]}...")
                        continue
            
            return ChatSession(
                session_id=session_id,
                messages=messages,
                start_time=start_time
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing log file: {e}")
            return ChatSession(
                session_id=session_id,
                messages=[],
                start_time=start_time
            )
    
    def get_trajectory_statistics(self, trajectory: List[TrajectoryStep]) -> Dict[str, Any]:
        """
        Get statistics about a trajectory
        
        Args:
            trajectory: List of trajectory steps
            
        Returns:
            Dictionary of statistics
        """
        if not trajectory:
            return {}
        
        emotions = [step.reward for step in trajectory]
        emotion_counts = {emotion: emotions.count(emotion) for emotion in EmotionState}
        
        # Calculate emotion distribution
        total_steps = len(trajectory)
        emotion_distribution = {
            emotion.value: count / total_steps 
            for emotion, count in emotion_counts.items()
        }
        
        # Calculate positive emotion ratio
        positive_emotions = [EmotionState.EXCITED, EmotionState.HAPPY]
        positive_count = sum(emotion_counts[e] for e in positive_emotions)
        positive_ratio = positive_count / total_steps if total_steps > 0 else 0
        
        # Session duration
        start_time = trajectory[0].timestamp
        end_time = trajectory[-1].timestamp
        duration_minutes = (end_time - start_time).total_seconds() / 60
        
        return {
            "total_steps": total_steps,
            "emotion_distribution": emotion_distribution,
            "positive_emotion_ratio": positive_ratio,
            "session_duration_minutes": duration_minutes,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "emotion_counts": {e.value: c for e, c in emotion_counts.items()}
        }
