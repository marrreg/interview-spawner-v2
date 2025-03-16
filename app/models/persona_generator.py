import os
import json
import uuid
import logging
from openai import OpenAI
import time
import concurrent.futures
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('persona_generator')

class Persona(BaseModel):
    """Represents a customer persona for interview simulation"""
    id: str
    name: str
    age: int
    gender: str
    occupation: str
    location: str
    demographics: Dict[str, Any]
    behaviors: List[str]
    goals: List[str]
    pain_points: List[str]
    motivations: List[str]
    challenges: List[str]
    personality: Dict[str, Any]
    background: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Persona':
        """Create a Persona instance from a dictionary"""
        if 'id' not in data:
            data['id'] = str(uuid.uuid4())
        return cls(**data)

class PersonaGenerator:
    """Generates realistic customer personas for interview simulation"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the persona generator
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            logger.error("No OpenAI API key provided or found in environment variables")
        else:
            logger.info("OpenAI API key found")
        self.client = OpenAI(api_key=self.api_key)
    
    def reflect_on_personas(self, context: str, num_personas: int = 5) -> List[Dict[str, str]]:
        """Reflect on which personas would be best suited for the given context
        
        Args:
            context: High-level context, industry, domain, product area, or problem statement
            num_personas: Number of personas to identify
            
        Returns:
            List[Dict[str, str]]: List of persona outlines with 'role' and 'description'
        """
        logger.info(f"Reflecting on {num_personas} personas for context: {context}")
        
        # Create the prompt for OpenAI
        system_prompt = """
        You are an expert in user research and market analysis.
        Your task is to reflect on which types of personas would be most valuable 
        to interview about the given topic or context.
        
        Use detailed chain-of-thought reasoning to consider:
        1. Who are the main stakeholders or user groups in this domain?
        2. Which personas would provide the most diverse and insightful perspectives?
        3. What specific roles or backgrounds would have valuable experiences with this topic?
        4. Which personas might have unique pain points, challenges, or needs?
        5. What combination of personas would provide comprehensive coverage of the topic?
        
        After your reasoning, provide a list of exactly the requested number of diverse personas 
        that would be valuable to interview, with a short description for each.
        
        Format your response as JSON with the following structure:
        {
            "reasoning": "Your chain-of-thought reasoning about which personas would be valuable...",
            "personas": [
                {
                    "role": "Concise role/title that defines this persona",
                    "description": "2-3 sentence description of who they are and why they're valuable to interview"
                },
                // Additional personas...
            ]
        }
        
        Be sure the entire response can be parsed as valid JSON.
        """
        
        user_prompt = f"""
        Context for persona identification: {context}
        
        Please identify {num_personas} diverse personas that would be most valuable to interview about this topic.
        """
        
        try:
            logger.info("Preparing to call OpenAI API for persona reflection")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            logger.info("Received response from OpenAI API for persona reflection")
            
            # Parse the response as JSON
            content = response.choices[0].message.content
            logger.info(f"Raw response content length: {len(content)}")
            
            # Extract the JSON part (in case there's additional text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.error(f"Failed to find valid JSON in the response: {content[:100]}...")
                return self._create_fallback_persona_list(context, num_personas)
                
            json_str = content[json_start:json_end]
            
            try:
                reflection_data = json.loads(json_str)
                logger.info(f"Successfully parsed JSON with keys: {list(reflection_data.keys())}")
                
                # Validate required fields
                if "personas" not in reflection_data or not isinstance(reflection_data["personas"], list):
                    logger.error("Reflection data missing 'personas' list")
                    return self._create_fallback_persona_list(context, num_personas)
                
                # Ensure we have the requested number of personas
                personas = reflection_data["personas"][:num_personas]
                while len(personas) < num_personas:
                    logger.warning(f"Not enough personas returned, adding fallback persona")
                    personas.append({
                        "role": f"General User {len(personas) + 1}",
                        "description": f"A typical user interested in {context} with general needs and concerns."
                    })
                
                # Log the reasoning if available
                if "reasoning" in reflection_data:
                    logger.info(f"Reasoning for persona selection: {reflection_data['reasoning'][:200]}...")
                
                logger.info(f"Successfully identified {len(personas)} personas")
                return personas
                
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error: {str(json_err)}")
                logger.error(f"Problematic JSON string: {json_str[:100]}...")
                return self._create_fallback_persona_list(context, num_personas)
            
        except Exception as e:
            logger.error(f"Error reflecting on personas: {str(e)}", exc_info=True)
            return self._create_fallback_persona_list(context, num_personas)
    
    def _create_fallback_persona_list(self, context: str, num_personas: int) -> List[Dict[str, str]]:
        """Create a list of fallback persona outlines if reflection fails
        
        Args:
            context: The original context provided
            num_personas: Number of personas to create
            
        Returns:
            List[Dict[str, str]]: List of basic persona outlines
        """
        logger.warning(f"Using fallback persona list for context: {context}")
        personas = []
        
        roles = ["Product Manager", "Business User", "Technical User", "New Customer", "Experienced User"]
        descriptions = [
            f"A product manager looking for solutions to improve their team's workflow in {context}",
            f"A business professional who needs to solve problems related to {context} without technical knowledge",
            f"A technical user with deep understanding of {context} who needs advanced solutions",
            f"Someone new to {context} who is exploring available solutions for the first time",
            f"A longtime user with extensive experience in {context} looking for improvements"
        ]
        
        for i in range(num_personas):
            idx = i % len(roles)
            personas.append({
                "role": roles[idx],
                "description": descriptions[idx]
            })
        
        return personas
    
    def generate_persona_from_outline(self, context: str, persona_outline: Dict[str, str]) -> Persona:
        """Generate a detailed persona from a role and description outline
        
        Args:
            context: High-level context, industry, domain, product area, or problem statement
            persona_outline: Dict containing 'role' and 'description' for the persona
            
        Returns:
            Persona: A generated persona object
        """
        logger.info(f"Generating detailed persona for role: {persona_outline['role']}")
        
        # Create the prompt for OpenAI
        system_prompt = """
        You are an expert in creating realistic customer personas for product research.
        Your task is to create one detailed, realistic persona for a potential customer/user
        in the provided context, based on the role and description provided.
        
        The persona should include:
        1. Basic demographic information (name, age, gender, occupation, location)
        2. Detailed behaviors relevant to the context
        3. Goals they're trying to achieve
        4. Pain points and frustrations they experience
        5. Motivations that drive their decisions
        6. Specific challenges they face in this industry/domain
        7. Personality traits that influence their preferences
        8. Background information that helps understand their perspective
        9. A concise description summarizing the persona
        
        Make this persona feel like a real person with nuanced characteristics, not a generic stereotype.
        Include unexpected but realistic details that make them memorable and authentic.
        
        Provide the output as a JSON object with the structure below:
        {
            "name": "Full Name",
            "age": age,
            "gender": "gender",
            "occupation": "job title",
            "location": "city, country",
            "demographics": {
                "income_level": "income bracket",
                "education": "education level",
                "family_status": "marital/family status",
                "other_relevant_demographics": "values"
            },
            "behaviors": ["behavior 1", "behavior 2"...],
            "goals": ["goal 1", "goal 2"...],
            "pain_points": ["pain point 1", "pain point 2"...],
            "motivations": ["motivation 1", "motivation 2"...],
            "challenges": ["challenge 1", "challenge 2"...],
            "personality": {
                "trait1": "description",
                "trait2": "description"
            },
            "background": "paragraph with relevant background",
            "description": "concise summary of this persona"
        }
        
        Be sure the entire response can be parsed as valid JSON.
        """
        
        user_prompt = f"""
        Context for persona creation: {context}
        
        Role: {persona_outline['role']}
        Description: {persona_outline['description']}
        
        Please create a detailed, realistic customer persona based on this role and description.
        """
        
        try:
            logger.info("Preparing to call OpenAI API")
            # Call OpenAI for persona generation
            logger.info(f"Using model: gpt-4o-mini with temperature: 0.7")
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=3000,
                temperature=0.7
            )
            
            logger.info("Received response from OpenAI API")
            
            # Parse the response as JSON
            content = response.choices[0].message.content
            logger.info(f"Raw response content: {content[:100]}...")  # Log the first 100 chars of response
            
            # Extract the JSON part (in case there's additional text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                logger.error(f"Failed to find valid JSON in the response: {content}")
                return self._create_fallback_persona(context, persona_outline)
                
            json_str = content[json_start:json_end]
            logger.info(f"Extracted JSON string length: {len(json_str)}")
            
            try:
                persona_data = json.loads(json_str)
                logger.info(f"Successfully parsed JSON with keys: {list(persona_data.keys())}")
                
                # Validate required fields
                required_fields = ["name", "age", "gender", "occupation", "location", 
                                  "demographics", "behaviors", "goals", "pain_points", 
                                  "motivations", "challenges", "personality", 
                                  "background", "description"]
                
                missing_fields = [field for field in required_fields if field not in persona_data]
                if missing_fields:
                    logger.error(f"Persona data missing required fields: {missing_fields}")
                    logger.info(f"Persona data contains: {list(persona_data.keys())}")
                    return self._create_fallback_persona(context, persona_outline)
                
                # Create and return the Persona object
                persona = Persona.from_dict(persona_data)
                logger.info(f"Successfully created persona: {persona.name}")
                return persona
                
            except json.JSONDecodeError as json_err:
                logger.error(f"JSON parsing error: {str(json_err)}")
                logger.error(f"Problematic JSON string: {json_str[:100]}...")
                return self._create_fallback_persona(context, persona_outline)
            
        except Exception as e:
            logger.error(f"Error generating persona: {str(e)}", exc_info=True)
            # Create a fallback persona if generation fails
            return self._create_fallback_persona(context, persona_outline)
    
    def _create_fallback_persona(self, context: str, persona_outline: Optional[Dict[str, str]] = None) -> Persona:
        """Create a basic fallback persona if generation fails
        
        Args:
            context: The original context provided
            persona_outline: Optional outline containing role and description
            
        Returns:
            Persona: A basic fallback persona
        """
        logger.warning(f"Using fallback persona for context: {context}")
        
        role = "Professional"
        description = f"A mid-career professional seeking solutions related to {context}."
        
        if persona_outline and "role" in persona_outline:
            role = persona_outline["role"]
        
        if persona_outline and "description" in persona_outline:
            description = persona_outline["description"]
        
        return Persona(
            id=str(uuid.uuid4()),
            name=f"Sample {role}",
            age=35,
            gender="Not specified",
            occupation=role,
            location="United States",
            demographics={
                "income_level": "Middle",
                "education": "Bachelor's degree",
                "family_status": "Not specified"
            },
            behaviors=["Researches options online", "Price-conscious"],
            goals=["Solve business problems efficiently", "Save time and money"],
            pain_points=["Frustrated with current solutions", "Lack of support"],
            motivations=["Improve productivity", "Reduce costs"],
            challenges=["Finding the right solution", "Implementation issues"],
            personality={
                "analytical": "Makes data-driven decisions",
                "pragmatic": "Focuses on practical outcomes"
            },
            background="Has been working in the industry for several years and is looking for better solutions.",
            description=description
        )
    
    def generate_personas(self, context: str, num_personas: int = 5) -> List[Persona]:
        """Generate multiple personas based on the given context using a two-step process:
        1. Reflect on which personas would be most valuable to interview
        2. Generate detailed personas for each identified persona type in parallel
        
        Args:
            context: High-level context, industry, domain, product area, or problem statement
            num_personas: Number of personas to generate
            
        Returns:
            List[Persona]: List of generated persona objects
        """
        logger.info(f"Starting two-step persona generation for context: {context}")
        
        # Step 1: Reflect on which personas would be most valuable to interview
        logger.info("Step 1: Reflecting on persona types")
        persona_outlines = self.reflect_on_personas(context, num_personas)
        logger.info(f"Identified {len(persona_outlines)} persona types")
        
        # Step 2: Generate detailed personas in parallel
        logger.info("Step 2: Generating detailed personas in parallel")
        personas = []
        
        # Use ThreadPoolExecutor to generate personas in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(num_personas, 5)) as executor:
            # Submit all persona generation tasks
            future_to_outline = {
                executor.submit(self.generate_persona_from_outline, context, outline): outline
                for outline in persona_outlines
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_outline):
                outline = future_to_outline[future]
                try:
                    persona = future.result()
                    personas.append(persona)
                    logger.info(f"Generated persona {len(personas)} of {num_personas}: {persona.name}")
                except Exception as e:
                    logger.error(f"Error generating persona for {outline['role']}: {str(e)}")
                    # Add a fallback persona if generation fails
                    personas.append(self._create_fallback_persona(context, outline))
        
        logger.info(f"Successfully generated {len(personas)} personas")
        return personas
    
    def generate_persona(self, context: str) -> Persona:
        """Generate a single persona based on the given context
        
        Args:
            context: High-level context, industry, domain, product area, or problem statement
            
        Returns:
            Persona: A generated persona object
        """
        # For backward compatibility, use the reflect and generate approach for a single persona
        persona_outlines = self.reflect_on_personas(context, 1)
        if persona_outlines:
            return self.generate_persona_from_outline(context, persona_outlines[0])
        else:
            return self._create_fallback_persona(context) 