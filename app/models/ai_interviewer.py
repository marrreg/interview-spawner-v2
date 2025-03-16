import os
import json
import uuid
from typing import List, Dict, Any, Optional
from openai import OpenAI
from pydantic import BaseModel, Field

class Message(BaseModel):
    """Represents a single message in a conversation"""
    role: str  # 'interviewer' or 'persona'
    content: str
    timestamp: float

class Conversation(BaseModel):
    """Represents a conversation between an interviewer and a persona"""
    id: str
    persona_id: str
    messages: List[Message] = []
    is_active: bool = True
    insights: List[str] = []
    summary: Optional[str] = None
    
    def add_message(self, role: str, content: str, timestamp: float) -> None:
        """Add a message to the conversation"""
        self.messages.append(Message(role=role, content=content, timestamp=timestamp))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert conversation to a dictionary"""
        return {
            "id": self.id,
            "persona_id": self.persona_id,
            "messages": [msg.dict() for msg in self.messages],
            "is_active": self.is_active,
            "insights": self.insights,
            "summary": self.summary
        }

class AIInterviewer:
    """AI-powered interviewer that conducts customer discovery conversations"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize the AI interviewer
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: OpenAI model to use for conversations
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
    
    def start_conversation(self, context: str, persona: Dict[str, Any]) -> Conversation:
        """Start a new conversation with a persona
        
        Args:
            context: High-level context for the conversation
            persona: Persona to interview
            
        Returns:
            Conversation: A new conversation object
        """
        # Create a new conversation
        conversation = Conversation(
            id=str(uuid.uuid4()),
            persona_id=persona["id"]
        )
        
        # Generate the initial message from the interviewer
        initial_message = self._generate_initial_message(context, persona)
        
        # Add the initial message to the conversation
        import time
        conversation.add_message(
            role="interviewer",
            content=initial_message,
            timestamp=time.time()
        )
        
        return conversation
    
    def _generate_initial_message(self, context: str, persona: Dict[str, Any]) -> str:
        """Generate the initial message from the interviewer
        
        Args:
            context: High-level context for the conversation
            persona: Persona to interview
            
        Returns:
            str: Initial message from the interviewer
        """
        system_prompt = f"""
        You are an experienced product researcher/product manager conducting a customer discovery interview. 
        You're interviewing a person with the following profile:
        
        Name: {persona['name']}
        Age: {persona['age']}
        Occupation: {persona['occupation']}
        Location: {persona['location']}
        
        Your goal is to understand their pain points, challenges, goals, and motivations related to the following context:
        {context}
        
        Begin the interview with a warm, professional introduction. Ask open-ended questions that encourage detailed responses.
        Follow best practices for product discovery interviews:
        1. Start with broad questions, then narrow down
        2. Use empathetic listening
        3. Ask "why" to dig deeper into motivations
        4. Avoid leading questions that suggest answers
        5. Focus on understanding problems, not selling solutions
        
        Craft a natural-sounding opening message that will engage this specific persona.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate an opening message for this interview."}
                ],
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating initial message: {str(e)}")
            return f"Hello {persona['name']}, thank you for joining me today. I'd like to learn about your experiences with {context}. Could you start by telling me about any challenges you face in this area?"
    
    def generate_persona_response(self, conversation: Conversation, context: str, persona: Dict[str, Any]) -> str:
        """Generate a response from the persona
        
        Args:
            conversation: The current conversation
            context: High-level context for the conversation
            persona: Persona information
            
        Returns:
            str: Generated response from the persona
        """
        # Convert messages to the format expected by the API
        messages_history = [
            {"role": "system", "content": self._create_persona_system_prompt(context, persona)}
        ]
        
        # Add conversation history
        for message in conversation.messages:
            role = "assistant" if message.role == "persona" else "user"
            messages_history.append({"role": role, "content": message.content})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_history,
                temperature=0.8,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating persona response: {str(e)}")
            return "I'm sorry, I'm having trouble articulating my thoughts right now."
    
    def generate_interviewer_response(self, conversation: Conversation, context: str, persona: Dict[str, Any]) -> str:
        """Generate a response from the interviewer
        
        Args:
            conversation: The current conversation
            context: High-level context for the conversation
            persona: Persona information
            
        Returns:
            str: Generated response from the interviewer
        """
        # Convert messages to the format expected by the API
        messages_history = [
            {"role": "system", "content": self._create_interviewer_system_prompt(context, persona)}
        ]
        
        # Add conversation history
        for message in conversation.messages:
            role = "assistant" if message.role == "interviewer" else "user"
            messages_history.append({"role": role, "content": message.content})
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages_history,
                temperature=0.7,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating interviewer response: {str(e)}")
            return "That's interesting. Could you tell me more about that?"
    
    def _create_persona_system_prompt(self, context: str, persona: Dict[str, Any]) -> str:
        """Create a system prompt for the persona
        
        Args:
            context: High-level context for the conversation
            persona: Persona information
            
        Returns:
            str: System prompt for the persona
        """
        return f"""
        You are roleplaying as a real person with the following characteristics:
        
        Name: {persona['name']}
        Age: {persona['age']}
        Gender: {persona['gender']}
        Occupation: {persona['occupation']}
        Location: {persona['location']}
        
        Demographics:
        {json.dumps(persona['demographics'], indent=2)}
        
        Behaviors:
        {json.dumps(persona['behaviors'], indent=2)}
        
        Goals:
        {json.dumps(persona['goals'], indent=2)}
        
        Pain Points:
        {json.dumps(persona['pain_points'], indent=2)}
        
        Motivations:
        {json.dumps(persona['motivations'], indent=2)}
        
        Challenges:
        {json.dumps(persona['challenges'], indent=2)}
        
        Personality:
        {json.dumps(persona['personality'], indent=2)}
        
        Background:
        {persona['background']}
        
        You are participating in a customer interview about: {context}
        
        Respond naturally as this person would, based on their characteristics. Be authentic, show emotions, and express your genuine pain points and challenges. Don't be overly formal - use natural language that fits your persona. Don't explicitly mention your persona details; instead, embody them in your responses.
        """
    
    def _create_interviewer_system_prompt(self, context: str, persona: Dict[str, Any]) -> str:
        """Create a system prompt for the interviewer
        
        Args:
            context: High-level context for the conversation
            persona: Persona information
            
        Returns:
            str: System prompt for the interviewer
        """
        return f"""
        You are an experienced product researcher/product manager conducting a customer discovery interview.
        
        You're interviewing: {persona['name']}, a {persona['age']}-year-old {persona['occupation']} from {persona['location']}.
        
        Context for this interview: {context}
        
        Your goal is to uncover deep insights about this person's:
        - Pain points and challenges
        - Goals and motivations
        - Current behaviors and workflows
        - Unmet needs and opportunities
        
        Follow these product discovery interview best practices:
        1. Ask open-ended questions
        2. Practice empathetic listening
        3. Probe deeper with "why" questions
        4. Avoid leading questions
        5. Focus on problems, not solutions
        6. Follow up on interesting points
        7. Validate understanding without judgment
        8. Create a safe, comfortable environment
        
        Keep your responses conversational and focused on getting the interviewee to share more details about their experiences.
        """
    
    def generate_insights(self, conversation: Conversation, context: str) -> List[str]:
        """Generate insights from the conversation
        
        Args:
            conversation: The conversation to analyze
            context: High-level context for the conversation
            
        Returns:
            List[str]: List of insights from the conversation
        """
        if len(conversation.messages) < 3:
            return []
        
        # Prepare conversation history
        conversation_text = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in conversation.messages])
        
        system_prompt = f"""
        You are an expert at analyzing customer discovery interviews and extracting key insights.
        
        Review the following conversation about {context} and identify 3-5 key insights.
        Focus on:
        1. Pain points and challenges
        2. Unmet needs
        3. Opportunities for innovation
        4. Surprising or unexpected revelations
        5. Underlying motivations
        
        Provide each insight as a concise, actionable statement that could inform product decisions.
        """
        
        user_prompt = f"""
        Here is the conversation to analyze:
        
        {conversation_text}
        
        Extract 3-5 key insights from this conversation.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            insights_text = response.choices[0].message.content
            
            # Parse insights into a list (assuming they're numbered or bulleted)
            import re
            insights = re.split(r'\n\s*[\d\-\*]+\.?\s*', insights_text)
            insights = [insight.strip() for insight in insights if insight.strip()]
            
            return insights
            
        except Exception as e:
            print(f"Error generating insights: {str(e)}")
            return []
    
    def generate_summary(self, conversation: Conversation, context: str) -> str:
        """Generate a summary of the conversation
        
        Args:
            conversation: The conversation to summarize
            context: High-level context for the conversation
            
        Returns:
            str: Summary of the conversation
        """
        if len(conversation.messages) < 4:
            return "Conversation not long enough to generate a meaningful summary."
        
        # Prepare conversation history
        conversation_text = "\n".join([f"{msg.role.upper()}: {msg.content}" for msg in conversation.messages])
        
        system_prompt = f"""
        You are an expert at summarizing customer discovery interviews.
        
        Review the following conversation about {context} and create a concise summary.
        Focus on:
        1. Key points discussed
        2. Main pain points identified
        3. Needs and desires expressed
        4. Behavioral patterns revealed
        5. Opportunities identified
        
        Keep the summary clear, concise, and focused on information that would be valuable for product development.
        """
        
        user_prompt = f"""
        Here is the conversation to summarize:
        
        {conversation_text}
        
        Provide a concise summary of this customer discovery conversation.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error generating summary: {str(e)}")
            return "Unable to generate summary due to an error." 