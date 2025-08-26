"""Language level evaluation agent using LangChain"""

from typing import List, Dict, Tuple, Optional
from langchain.agents import initialize_agent, AgentType
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from models import LanguageLevel, ChatMessage


class LanguageLevelAgent:
    """Agent-based language level evaluator"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """Initialize the language level evaluation agent"""
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=0.3  # Lower temperature for more consistent evaluation
        )
        
        self.evaluation_prompt = PromptTemplate(
            input_variables=["messages", "level_descriptions"],
            template="""You are an expert in Chinese language education, specifically evaluating children's Chinese proficiency levels.

Analyze the following conversation messages and determine the student's Chinese language level.

Language Levels:
{level_descriptions}

Recent Messages:
{messages}

Based on the messages, evaluate:
1. Number of Chinese characters used
2. Average sentence complexity and length
3. Presence of complex grammatical structures
4. Use of connectors and advanced vocabulary
5. Overall communication fluency

Provide your evaluation in the following format:
LEVEL: [L1/L2/L3/L4/L5]
CONFIDENCE: [0.0-1.0]
REASONING: [Brief explanation of your assessment]
"""
        )
        
        self.level_descriptions = """
L1 (Emerging Awareness): 
- Uses 0-2 Chinese characters per conversation
- Very simple English sentences (avg 5 words)
- No complex structures
- Single word responses common

L2 (Basic Expression):
- Uses 1-3 Chinese characters
- Simple sentences (avg 7 words)
- Beginning to form basic phrases
- Can say simple greetings and express basic needs

L3 (Sentence Development):
- Uses 3-5 Chinese characters
- Moderate sentence length (avg 10 words)
- Uses basic connectors (and, but)
- Can form complete sentences with reasons

L4 (Interactive Communication):
- Uses 5-8 Chinese characters
- Longer sentences (avg 12 words)
- Complex structures present
- Can engage in back-and-forth conversation

L5 (Structured & Logical Speech):
- Uses 8+ Chinese characters
- Complex sentences (avg 15+ words)
- Advanced connectors and structures
- Can explain reasoning and tell stories
"""
    
    def evaluate_level(self, messages: List[ChatMessage]) -> Tuple[LanguageLevel, float]:
        """
        Evaluate language level from chat messages using the agent
        
        Args:
            messages: List of chat messages to analyze
            
        Returns:
            Tuple of (LanguageLevel, confidence_score)
        """
        if len(messages) < 3:
            return LanguageLevel.L1, 0.5
        
        # Extract user messages only
        user_messages = [m for m in messages[-10:] if m.role == "user"]
        if not user_messages:
            return LanguageLevel.L1, 0.5
        
        # Format messages for the agent
        formatted_messages = "\n".join([
            f"Message {i+1}: {msg.content}"
            for i, msg in enumerate(user_messages)
        ])
        
        try:
            # Create the evaluation prompt
            prompt = self.evaluation_prompt.format(
                messages=formatted_messages,
                level_descriptions=self.level_descriptions
            )
            
            # Get evaluation from the agent
            response = self.llm.invoke([HumanMessage(content=prompt)])
            
            # Parse the response
            return self._parse_evaluation_response(response.content)
            
        except Exception as e:
            print(f"Error in language level evaluation: {e}")
            # Fallback to simple evaluation
            return self._simple_evaluation(user_messages)
    
    def _parse_evaluation_response(self, response: str) -> Tuple[LanguageLevel, float]:
        """Parse the agent's evaluation response"""
        lines = response.strip().split('\n')
        
        level = LanguageLevel.L1
        confidence = 0.5
        
        for line in lines:
            if line.startswith("LEVEL:"):
                level_str = line.split(":")[1].strip()
                try:
                    level = LanguageLevel[level_str]
                except:
                    pass
            elif line.startswith("CONFIDENCE:"):
                conf_str = line.split(":")[1].strip()
                try:
                    confidence = float(conf_str)
                except:
                    pass
        
        return level, confidence
    
    def _simple_evaluation(self, messages: List[ChatMessage]) -> Tuple[LanguageLevel, float]:
        """Simple fallback evaluation based on message characteristics"""
        # Count Chinese characters
        chinese_char_count = 0
        total_words = 0
        
        for msg in messages:
            for char in msg.content:
                if '\u4e00' <= char <= '\u9fff':
                    chinese_char_count += 1
            total_words += len(msg.content.split())
        
        avg_words = total_words / len(messages) if messages else 0
        avg_chinese = chinese_char_count / len(messages) if messages else 0
        
        # Determine level based on simple metrics
        if avg_chinese >= 8 and avg_words >= 15:
            return LanguageLevel.L5, 0.7
        elif avg_chinese >= 5 and avg_words >= 12:
            return LanguageLevel.L4, 0.7
        elif avg_chinese >= 3 and avg_words >= 10:
            return LanguageLevel.L3, 0.7
        elif avg_chinese >= 1 and avg_words >= 7:
            return LanguageLevel.L2, 0.7
        else:
            return LanguageLevel.L1, 0.7
    
    def get_level_feedback(self, level: LanguageLevel) -> str:
        """Get feedback message for the current level"""
        feedback_messages = {
            LanguageLevel.L1: "Just starting the Chinese journey! Focus on single words and sounds.",
            LanguageLevel.L2: "Making progress! Starting to use simple phrases.",
            LanguageLevel.L3: "Great improvement! Building complete sentences.",
            LanguageLevel.L4: "Excellent progress! Engaging in real conversations.",
            LanguageLevel.L5: "Advanced level! Complex communication skills demonstrated."
        }
        return feedback_messages.get(level, "Keep practicing!")


# For backward compatibility
LanguageLevelEvaluator = LanguageLevelAgent
