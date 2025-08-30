"""BERT-based emotion detection for the teaching agent"""

import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from typing import Optional, Dict, List
import logging

from helper.models import EmotionState


class BERTEmotionDetector:
    """BERT-based emotion detection using Hugging Face transformers"""
    
    def __init__(self, model_name: str = "j-hartmann/emotion-english-distilroberta-base"):
        """
        Initialize the BERT-based emotion detector
        
        Args:
            model_name: Hugging Face model for emotion detection
        """
        try:
            self.classifier = pipeline(
                "sentiment-analysis",
                model=model_name,
                device=0 if torch.cuda.is_available() else -1
            )
            logging.info(f"Loaded emotion detection model: {model_name}")
        except Exception as e:
            logging.error(f"Failed to load model {model_name}: {e}")
            # Fallback to a simpler model if the main one fails
            try:
                self.classifier = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1
                )
                logging.info("Using fallback sentiment model")
            except:
                # Final fallback to rule-based if ML models fail
                self.classifier = None
                logging.warning("Using rule-based emotion detection as fallback")
    
    def detect_emotion(self, text: str) -> EmotionState:
        """
        Detect emotion from user input using BERT
        
        Args:
            text: User input text
            
        Returns:
            Detected EmotionState
        """
        if not self.classifier:
            return self._rule_based_detection(text)
        
        try:
            # Get predictions from the model
            results = self.classifier(text, top_k=None)
            
            # Map model emotions to our EmotionState enum
            emotion_mapping = {
                "joy": EmotionState.HAPPY,
                "happiness": EmotionState.HAPPY,
                "positive": EmotionState.HAPPY,
                "excitement": EmotionState.EXCITED,
                "surprise": EmotionState.EXCITED,
                "sadness": EmotionState.SAD,
                "negative": EmotionState.SAD,
                "fear": EmotionState.FRUSTRATED,
                "anger": EmotionState.FRUSTRATED,
                "disgust": EmotionState.FRUSTRATED,
                "neutral": EmotionState.NEUTRAL,
                "love": EmotionState.HAPPY,
            }
            
            # Find the best matching emotion
            for result in results:
                label = result['label'].lower()
                for key, emotion_state in emotion_mapping.items():
                    if key in label:
                        return emotion_state
            
            # Default to neutral if no match
            return EmotionState.NEUTRAL
            
        except Exception as e:
            logging.error(f"Error in emotion detection: {e}")
            return self._rule_based_detection(text)
    
    def _rule_based_detection(self, text: str) -> EmotionState:
        """Fallback rule-based emotion detection"""
        text_lower = text.lower()
        
        # Simple keyword matching as fallback
        emotion_keywords = {
            EmotionState.EXCITED: ["wow", "awesome", "cool", "amazing", "yay", "fun", "great", "love", "!"],
            EmotionState.HAPPY: ["happy", "good", "nice", "like", "yes", "okay", "thanks"],
            EmotionState.FRUSTRATED: ["hard", "difficult", "can't", "don't know", "confused", "no", "wrong"],
            EmotionState.TIRED: ["tired", "sleepy", "boring", "enough", "stop", "later"],
            EmotionState.SAD: ["sad", "miss", "lonely", "cry", "hurt"],
        }
        
        emotion_scores = {}
        for emotion, keywords in emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        return EmotionState.NEUTRAL
    
    def get_emotion_confidence(self, text: str) -> Dict[str, float]:
        """
        Get confidence scores for each emotion
        
        Args:
            text: User input text
            
        Returns:
            Dictionary of emotion states and their confidence scores
        """
        if not self.classifier:
            # Simple confidence for rule-based
            detected = self._rule_based_detection(text)
            return {emotion.value: 1.0 if emotion == detected else 0.0 
                    for emotion in EmotionState}
        
        try:
            results = self.classifier(text, top_k=None)
            confidence_dict = {}
            
            # Initialize all emotions with 0 confidence
            for emotion in EmotionState:
                confidence_dict[emotion.value] = 0.0
            
            # Map and aggregate confidence scores
            emotion_mapping = {
                "joy": EmotionState.HAPPY,
                "happiness": EmotionState.HAPPY,
                "positive": EmotionState.HAPPY,
                "excitement": EmotionState.EXCITED,
                "surprise": EmotionState.EXCITED,
                "sadness": EmotionState.SAD,
                "negative": EmotionState.SAD,
                "fear": EmotionState.FRUSTRATED,
                "anger": EmotionState.FRUSTRATED,
                "disgust": EmotionState.FRUSTRATED,
                "neutral": EmotionState.NEUTRAL,
                "love": EmotionState.HAPPY,
            }
            
            for result in results:
                label = result['label'].lower()
                score = result['score']
                
                for key, emotion_state in emotion_mapping.items():
                    if key in label:
                        confidence_dict[emotion_state.value] = max(
                            confidence_dict[emotion_state.value], 
                            score
                        )
                        break
            
            return confidence_dict
            
        except Exception as e:
            logging.error(f"Error getting emotion confidence: {e}")
            detected = self._rule_based_detection(text)
            return {emotion.value: 1.0 if emotion == detected else 0.0 
                    for emotion in EmotionState}


# For backward compatibility
EmotionDetector = BERTEmotionDetector
