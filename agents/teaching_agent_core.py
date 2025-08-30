"""Core teaching agent implementation without web dependencies"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import ChatMessageHistory

from helper.models import (
    TeachingContext, StudentProfile, EmotionState, 
    LanguageLevel, TeachingPolicy, ChatMessage
)
from prompts import (
    teaching_prompt_template, teaching_character, 
    teaching_user_profile, teaching_rules, level_instructions
)
from helper.utils import (
    WordManager, SessionStorage, get_encouragement
)
from helper.emotion_detector import EmotionDetector
from agents.language_level_agent import LanguageLevelAgent
from agents.policy_generator_agent import PolicyGeneratorAgent


class TeachingAgentCore:
    """Core teaching agent without web dependencies"""
    
    def __init__(self, session_id: str, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        self.session_id = session_id
        self.storage = SessionStorage()
        
        # Load or create student profile
        self.student_profile = self.storage.load_profile(session_id)
        if not self.student_profile:
            self.student_profile = StudentProfile(session_id=session_id)
        
        # Initialize components
        self.word_manager = WordManager()
        self.emotion_detector = EmotionDetector()
        self.level_evaluator = LanguageLevelAgent(api_key, base_url, model_name)
        self.policy_generator = PolicyGeneratorAgent(api_key, base_url, model_name)
        
        # Initialize teaching context
        self.context = TeachingContext(
            student_profile=self.student_profile,
            current_word_category=self.word_manager.get_random_category()
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=0.7
        )
        
        # Initialize agent
        self.agent_executor = self._build_agent()
        
        # Track session
        self.student_profile.session_count += 1
    
    def _get_tools(self) -> List[Tool]:
        """Get available tools for the agent"""
        return [
            DuckDuckGoSearchResults(num_results=2),
            Tool(
                name="GetChineseWord",
                func=self._get_chinese_word,
                description="Get a Chinese word appropriate for the student's level and current context"
            ),
            Tool(
                name="CheckWordMastery",
                func=self._check_word_mastery,
                description="Check the student's mastery level for a specific Chinese word"
            ),
            Tool(
                name="GetEncouragement",
                func=lambda _: get_encouragement(),
                description="Get an encouraging phrase to motivate the student"
            )
        ]
    
    def _get_chinese_word(self, request: str) -> str:
        """Get an appropriate Chinese word based on context"""
        word = self.word_manager.get_word_for_level(
            self.student_profile.language_level,
            self.context.current_word_category
        )
        
        if word:
            return f"Word: {word.chinese} ({word.pinyin}) - {word.english} {word.emoji or ''}"
        return "No appropriate word found for current level"
    
    def _check_word_mastery(self, word: str) -> str:
        """Check student's mastery of a word"""
        mastery = self.student_profile.get_mastery_level(word)
        if mastery >= 80:
            return f"Great mastery of '{word}'! (Level: {mastery}/100)"
        elif mastery >= 50:
            return f"Good progress with '{word}'! (Level: {mastery}/100)"
        elif mastery > 0:
            return f"Still learning '{word}' (Level: {mastery}/100)"
        else:
            return f"'{word}' is new!"
    
    def _build_agent(self) -> AgentExecutor:
        """Build the ReAct agent"""
        tools = self._get_tools()
        
        # Get level-specific instructions
        level_instructions_text = level_instructions.get(
            self.student_profile.language_level.value,
            level_instructions["L1"]
        )
        
        # Generate initial policy
        policy = self.policy_generator.generate_policy(
            self.context.current_emotion,
            self.student_profile.language_level,
            self.context.emotion_trend
        )
        
        # Create prompt
        prompt = PromptTemplate.from_template(teaching_prompt_template)
        prompt = prompt.partial(
            character=teaching_character,
            user_profile=teaching_user_profile,
            rule=teaching_rules + "\n\n" + policy,
            emotion_state=self.context.current_emotion.value,
            emotion_trend=self.context.emotion_trend.value,
            needs_intervention=str(self.context.needs_intervention),
            word_category=self.context.current_word_category,
            language_level=self.student_profile.language_level.value,
            level_specific_instructions=level_instructions_text
        )
        
        # Create agent
        agent = create_react_agent(self.llm, tools, prompt)
        
        # Create memory
        chat_memory = ChatMessageHistory()
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            chat_memory=chat_memory,
            input_key="input",
            output_key="output"
        )
        
        return AgentExecutor(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=False,  # Set to True for debugging
            max_iterations=5,
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )
    
    def process_input(self, user_input: str) -> str:
        """Process user input and generate response"""
        # Detect emotion
        emotion = self.emotion_detector.detect_emotion(user_input)
        self.context.current_emotion = emotion
        
        # Add message to context
        self.context.add_message("user", user_input, emotion)
        
        # Update language level if needed
        if len(self.context.session_messages) % 5 == 0:  # Check every 5 messages
            new_level, confidence = self.level_evaluator.evaluate_level(
                self.context.session_messages
            )
            if confidence > 0.7 and new_level != self.student_profile.language_level:
                self.student_profile.language_level = new_level
                print(f"[System] Language level updated to {new_level.value}")
        
        # Check if we need to rebuild agent (for policy updates)
        if self.context.needs_intervention or len(self.context.session_messages) % 10 == 0:
            self.agent_executor = self._build_agent()
        
        # Generate response
        try:
            full_input = f"Student says: {user_input}"
            response = self.agent_executor.invoke({"input": full_input})
            output = response["output"]
            
            # Extract Chinese words from response for tracking
            chinese_words = self._extract_chinese_words(output)
            self.context.add_message("assistant", output)
            
            # Update word mastery
            for word in chinese_words:
                self.student_profile.add_learned_word(word, 5)
            
            return output
            
        except Exception as e:
            error_msg = f"Oops! Something went wrong. Let's try again! 😊"
            self.context.add_message("assistant", error_msg)
            return error_msg
    
    def _extract_chinese_words(self, text: str) -> List[str]:
        """Extract Chinese characters from text"""
        chinese_words = []
        current_word = ""
        
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                current_word += char
            else:
                if current_word:
                    chinese_words.append(current_word)
                    current_word = ""
        
        if current_word:
            chinese_words.append(current_word)
        
        return chinese_words
    
    def get_session_summary(self) -> Dict[str, any]:
        """Get summary of current session"""
        duration = self.context.get_session_duration()
        
        return {
            "session_id": self.session_id,
            "duration_minutes": duration,
            "messages_count": len(self.context.session_messages),
            "current_level": self.student_profile.language_level.value,
            "current_emotion": self.context.current_emotion.value,
            "emotion_trend": self.context.emotion_trend.value,
            "words_learned": len([w for w, m in self.student_profile.learned_words.items() if m > 0]),
            "total_sessions": self.student_profile.session_count
        }
    
    def save_session(self):
        """Save current session data"""
        # Update total interaction time
        self.student_profile.total_interaction_time += self.context.get_session_duration()
        
        # Save profile
        self.storage.save_profile(self.student_profile)
        
        # Save session log
        self.storage.save_session_log(self.session_id, self.context.session_messages)
    
    def end_session(self) -> str:
        """End the session and return farewell message"""
        self.save_session()
        
        # Generate appropriate farewell based on emotion
        if self.context.current_emotion in [EmotionState.HAPPY, EmotionState.EXCITED]:
            farewell = "That was so much fun! See you next time, buddy! 🌟 再见 (zàijiàn)!"
        elif self.context.current_emotion in [EmotionState.TIRED, EmotionState.SAD]:
            farewell = "Rest well, my friend! Tomorrow will be even better! 💤 晚安 (wǎn'ān)!"
        else:
            farewell = "Great job today! Can't wait to play again! 👋 再见 (zàijiàn)!"
        
        return farewell


class SimpleTeachingAgent:
    """Simplified interface for CLI usage"""
    
    def __init__(self, session_id: str, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        self.core = TeachingAgentCore(session_id, api_key, base_url, model_name)
    
    def chat(self, message: str) -> str:
        """Simple chat interface"""
        return self.core.process_input(message)
    
    def get_summary(self) -> Dict[str, any]:
        """Get session summary"""
        return self.core.get_session_summary()
    
    def end(self) -> str:
        """End session"""
        return self.core.end_session()
