"""Policy generation agent using LangChain"""

from typing import Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from helper.models import EmotionState, LanguageLevel, EmotionTrend


class PolicyGeneratorAgent:
    """Agent-based teaching policy generator"""
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """Initialize the policy generation agent"""
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,
            model=model_name,
            temperature=0.7  # Moderate temperature for creative but focused policies
        )
        
        self.policy_prompt = PromptTemplate(
            input_variables=["emotion_state", "language_level", "emotion_trend", "context"],
            template="""You are an expert in child education and adaptive teaching strategies for Chinese language learning.

Generate a specific teaching policy based on the current context:

Current Student State:
- Emotional State: {emotion_state}
- Language Level: {language_level}
- Emotion Trend: {emotion_trend}
- Additional Context: {context}

Create an adaptive teaching policy that:
1. Responds appropriately to the student's emotional state
2. Matches activities to their language level
3. Considers the emotion trend (improving, stable, declining)
4. Provides specific, actionable guidance
5. Maintains engagement and fun

Format your policy as clear, concise instructions that the teaching agent can follow.

ADAPTIVE TEACHING POLICY:
"""
        )
        
        self.system_message = SystemMessage(content="""You are an expert in adaptive teaching strategies for young language learners. 
Your policies should be:
- Emotionally responsive and empathetic
- Developmentally appropriate
- Engaging and playful
- Specific and actionable
- Focused on maintaining a positive learning experience""")
    
    def generate_policy(self, 
                       emotion: EmotionState, 
                       level: LanguageLevel, 
                       trend: EmotionTrend,
                       context: Optional[Dict[str, str]] = None) -> str:
        """
        Generate a teaching policy using the agent
        
        Args:
            emotion: Current emotion state
            level: Current language level
            trend: Emotion trend
            context: Additional context (optional)
            
        Returns:
            Generated teaching policy string
        """
        try:
            # Create context string
            context_str = ""
            if context:
                context_items = [f"{k}: {v}" for k, v in context.items()]
                context_str = "; ".join(context_items)
            else:
                context_str = "No additional context"
            
            # Create the prompt
            prompt = self.policy_prompt.format(
                emotion_state=self._get_emotion_description(emotion),
                language_level=self._get_level_description(level),
                emotion_trend=trend.value,
                context=context_str
            )
            
            # Generate policy
            messages = [self.system_message, HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating policy: {e}")
            # Fallback to simple policy
            return self._get_fallback_policy(emotion, level, trend)
    
    def _get_emotion_description(self, emotion: EmotionState) -> str:
        """Get detailed description of emotion state"""
        descriptions = {
            EmotionState.EXCITED: "Excited and energetic - high engagement and enthusiasm",
            EmotionState.HAPPY: "Happy and positive - good mood and receptive to learning",
            EmotionState.NEUTRAL: "Neutral - calm but may need engagement boost",
            EmotionState.FRUSTRATED: "Frustrated - struggling and needs support",
            EmotionState.TIRED: "Tired - low energy, needs gentle approach",
            EmotionState.SAD: "Sad - needs emotional support and comfort"
        }
        return descriptions.get(emotion, emotion.value)
    
    def _get_level_description(self, level: LanguageLevel) -> str:
        """Get detailed description of language level"""
        descriptions = {
            LanguageLevel.L1: "L1 (Emerging Awareness) - Just beginning, focus on single words",
            LanguageLevel.L2: "L2 (Basic Expression) - Simple phrases and basic patterns",
            LanguageLevel.L3: "L3 (Sentence Development) - Building complete sentences",
            LanguageLevel.L4: "L4 (Interactive Communication) - Conversational level",
            LanguageLevel.L5: "L5 (Structured & Logical) - Advanced communication"
        }
        return descriptions.get(level, level.value)
    
    def _get_fallback_policy(self, emotion: EmotionState, level: LanguageLevel, trend: EmotionTrend) -> str:
        """Fallback policy generation"""
        # Emotion-based strategies
        emotion_strategies = {
            EmotionState.EXCITED: "Match their excitement! Introduce new words quickly and celebrate their enthusiasm.",
            EmotionState.HAPPY: "Keep the positive momentum going with fun activities and gentle challenges.",
            EmotionState.NEUTRAL: "Spark interest with a fun question or game to engage them.",
            EmotionState.FRUSTRATED: "Slow down, offer encouragement, and switch to easier content or a fun break.",
            EmotionState.TIRED: "Keep it light and easy, maybe suggest a calming activity or story.",
            EmotionState.SAD: "Show empathy first, then gently redirect to something comforting and fun."
        }
        
        # Level-based focus
        level_focus = {
            LanguageLevel.L1: "Focus on single words with sounds and visual associations.",
            LanguageLevel.L2: "Practice simple 2-3 word phrases and basic patterns.",
            LanguageLevel.L3: "Encourage complete sentences and simple explanations.",
            LanguageLevel.L4: "Engage in conversations and discuss feelings.",
            LanguageLevel.L5: "Explore stories and complex ideas together."
        }
        
        policy = f"""
ADAPTIVE TEACHING POLICY:
Emotion Response: {emotion_strategies.get(emotion, "Be attentive and responsive.")}
Level Focus: {level_focus.get(level, "Adapt to their current ability.")}
Trend Action: {"Maintain current approach" if trend == EmotionTrend.STABLE else "Adjust energy and difficulty"}
"""
        return policy.strip()
    
    def generate_intervention_policy(self, emotion: EmotionState, reason: str) -> str:
        """Generate a specific intervention policy for emotional support"""
        try:
            intervention_prompt = f"""The student is experiencing {emotion.value} emotions. 
Reason: {reason}

Generate a brief, specific intervention strategy to help the student feel better and re-engage with learning.
Focus on emotional support first, then gentle re-engagement with Chinese learning.

INTERVENTION STRATEGY:"""

            messages = [self.system_message, HumanMessage(content=intervention_prompt)]
            response = self.llm.invoke(messages)
            
            return response.content.strip()
            
        except Exception as e:
            print(f"Error generating intervention: {e}")
            
            # Fallback interventions
            interventions = {
                EmotionState.FRUSTRATED: "Take a break with a fun game. Offer specific praise for effort. Switch to easier content they've mastered.",
                EmotionState.SAD: "Acknowledge their feelings warmly. Share a comforting story. Introduce mood-lifting activities.",
                EmotionState.TIRED: "Suggest a calm activity. Use gentle, soothing tone. Keep interactions brief and light."
            }
            return interventions.get(emotion, "Provide emotional support and adjust approach to student needs.")


# For backward compatibility
PolicyGenerator = PolicyGeneratorAgent
