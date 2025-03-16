import os
import time
import uuid
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json

from .persona_generator import PersonaGenerator, Persona
from .ai_interviewer import AIInterviewer, Conversation
from .insight_aggregator import InsightAggregator

class Simulation:
    """Represents a customer discovery simulation"""
    
    def __init__(self, id: str, context: str, num_personas: int = 5, max_turns: int = 10):
        """Initialize a simulation
        
        Args:
            id: Unique identifier for the simulation
            context: High-level context for the simulation
            num_personas: Number of personas to generate
            max_turns: Maximum number of conversation turns per persona
        """
        self.id = id
        self.context = context
        self.num_personas = num_personas
        self.max_turns = max_turns
        self.personas: List[Persona] = []
        self.conversations: Dict[str, Conversation] = {}  # persona_id -> conversation
        self.status = "created"  # created, generating_personas, ready, running, completed, error
        self.aggregated_insights: List[Dict[str, Any]] = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the simulation to a dictionary"""
        return {
            "id": self.id,
            "context": self.context,
            "num_personas": self.num_personas,
            "max_turns": self.max_turns,
            "status": self.status,
            "personas_count": len(self.personas),
            "conversations_count": len(self.conversations),
            "insights_count": len(self.aggregated_insights),
            "start_time": self.start_time,
            "end_time": self.end_time,
            "error": self.error
        }

class SimulationManager:
    """Manages customer discovery simulations"""
    
    def __init__(self):
        """Initialize the simulation manager"""
        self.simulations: Dict[str, Simulation] = {}
        self.persona_generator = PersonaGenerator()
        self.ai_interviewer = AIInterviewer()
        self.insight_aggregator = InsightAggregator()
        self.threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()  # Add a lock for thread safety
    
    def create_simulation(self, context: str, num_personas: int = 5, max_turns: int = 10) -> str:
        """Create a new simulation
        
        Args:
            context: High-level context for the simulation
            num_personas: Number of personas to generate
            max_turns: Maximum number of conversation turns per persona
        
        Returns:
            str: Simulation ID
        """
        simulation_id = str(uuid.uuid4())
        
        # Create a new simulation
        simulation = Simulation(
            id=simulation_id,
            context=context,
            num_personas=num_personas,
            max_turns=max_turns
        )
        
        # Store the simulation
        self.simulations[simulation_id] = simulation
        
        # Start generating personas in the background
        self._generate_personas_async(simulation_id)
        
        return simulation_id
    
    def _generate_personas_async(self, simulation_id: str) -> None:
        """Generate personas in the background
        
        Args:
            simulation_id: Simulation ID
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return
        
        # Update simulation status
        simulation.status = "generating_personas"
        
        # Define the async task
        def generate_personas_task():
            try:
                # Generate personas using the two-step process
                # This will internally:
                # 1. Reflect on which personas would be valuable (with chain of thought reasoning)
                # 2. Generate all detailed personas in parallel
                personas = self.persona_generator.generate_personas(
                    context=simulation.context,
                    num_personas=simulation.num_personas
                )
                
                # Store personas
                simulation.personas = personas
                
                # Update simulation status
                simulation.status = "ready"
                
            except Exception as e:
                # Handle error
                simulation.status = "error"
                simulation.error = str(e)
                print(f"Error generating personas for simulation {simulation_id}: {str(e)}")
        
        # Start the task in a background thread
        thread = threading.Thread(target=generate_personas_task)
        thread.daemon = True
        thread.start()
        
        # Store the thread
        self.threads[simulation_id] = thread
    
    def start_simulation(self, simulation_id: str) -> bool:
        """Start a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            bool: Success
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation or simulation.status != "ready":
            return False
        
        # Update simulation status
        simulation.status = "running"
        simulation.start_time = time.time()
        
        # Start the simulation in the background
        self._run_simulation_async(simulation_id)
        
        return True
    
    def _run_simulation_async(self, simulation_id: str) -> None:
        """Run a simulation in the background
        
        Args:
            simulation_id: Simulation ID
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return
        
        # Define the async task
        def run_simulation_task():
            try:
                # Start conversations for each persona
                for persona in simulation.personas:
                    conversation = self.ai_interviewer.start_conversation(
                        context=simulation.context,
                        persona=persona.dict()
                    )
                    simulation.conversations[persona.id] = conversation
                
                # Create a list to keep track of conversation threads
                conversation_threads = []
                
                # Function to run a single conversation
                def run_conversation(persona):
                    conversation = simulation.conversations.get(persona.id)
                    if not conversation:
                        return
                    
                    # Run conversation for max_turns or until stopped
                    for turn in range(simulation.max_turns):
                        # Check if simulation is still running
                        if simulation.status != "running":
                            break
                        
                        if not conversation.is_active:
                            break
                            
                        # Generate persona response
                        if len(conversation.messages) % 2 == 1:  # interviewer spoke last
                            persona_response = self.ai_interviewer.generate_persona_response(
                                conversation=conversation,
                                context=simulation.context,
                                persona=persona.dict()
                            )
                            
                            # Add message to conversation
                            conversation.add_message(
                                role="persona",
                                content=persona_response,
                                timestamp=time.time()
                            )
                        
                        # Generate interviewer response
                        else:  # persona spoke last
                            interviewer_response = self.ai_interviewer.generate_interviewer_response(
                                conversation=conversation,
                                context=simulation.context,
                                persona=persona.dict()
                            )
                            
                            # Add message to conversation
                            conversation.add_message(
                                role="interviewer",
                                content=interviewer_response,
                                timestamp=time.time()
                            )
                        
                        # Generate insights after several turns
                        if len(conversation.messages) >= 6 and len(conversation.messages) % 2 == 0:
                            insights = self.ai_interviewer.generate_insights(
                                conversation=conversation,
                                context=simulation.context
                            )
                            conversation.insights = insights
                        
                        # Small delay between turns
                        time.sleep(1)
                    
                    # Generate summary once conversation is done
                    summary = self.ai_interviewer.generate_summary(
                        conversation=conversation,
                        context=simulation.context
                    )
                    conversation.summary = summary
                
                # Start a thread for each conversation
                for persona in simulation.personas:
                    thread = threading.Thread(target=run_conversation, args=(persona,))
                    thread.daemon = True
                    thread.start()
                    conversation_threads.append(thread)
                
                # Wait for all conversation threads to complete
                for thread in conversation_threads:
                    thread.join()
                
                # Aggregate insights across all conversations
                self._aggregate_insights(simulation_id)
                
                # Update simulation status
                simulation.status = "completed"
                simulation.end_time = time.time()
                
            except Exception as e:
                simulation.status = "error"
                simulation.error = str(e)
                simulation.end_time = time.time()
        
        # Create and start the thread
        thread = threading.Thread(target=run_simulation_task)
        thread.daemon = True
        thread.start()
        self.threads[simulation_id] = thread
    
    def _aggregate_insights(self, simulation_id: str) -> None:
        """Aggregate insights from all conversations
        
        Args:
            simulation_id: Simulation ID
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return
        
        # Collect all insights from active conversations
        all_insights = []
        
        with self.lock:  # Use lock to ensure thread safety
            for persona in simulation.personas:
                conversation = simulation.conversations.get(persona.id)
                if conversation and conversation.insights:
                    for insight in conversation.insights:
                        all_insights.append({
                            "insight": insight,
                            "persona_id": persona.id,
                            "persona_name": persona.name,
                            "conversation_id": conversation.id
                        })
            
            # Use the insight aggregator to identify common themes
            if all_insights:
                aggregated = self.insight_aggregator.aggregate_insights(
                    insights=all_insights,
                    context=simulation.context
                )
                simulation.aggregated_insights = aggregated
    
    def stop_simulation(self, simulation_id: str) -> bool:
        """Stop a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            bool: Success
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation or simulation.status != "running":
            return False
        
        # Update simulation status
        simulation.status = "completed"
        simulation.end_time = time.time()
        
        return True
    
    def get_simulation(self, simulation_id: str) -> Optional[Simulation]:
        """Get a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            Optional[Simulation]: Simulation or None if not found
        """
        return self.simulations.get(simulation_id)
    
    def get_personas(self, simulation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get personas for a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of personas or None if not found
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return [persona.dict() for persona in simulation.personas]
    
    def get_conversations(self, simulation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get conversations for a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of conversations or None if not found
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return [conversation.to_dict() for conversation in simulation.conversations.values()]
    
    def get_insights(self, simulation_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get aggregated insights for a simulation
        
        Args:
            simulation_id: Simulation ID
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of insights or None if not found
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        return simulation.aggregated_insights
    
    def get_progress(self, simulation_id: str) -> Optional[Dict[str, Any]]:
        """Get the progress of a simulation
        
        Args:
            simulation_id: Simulation ID
            
        Returns:
            Optional[Dict[str, Any]]: Progress information
        """
        simulation = self.simulations.get(simulation_id)
        if not simulation:
            return None
        
        if simulation.status not in ["running", "completed"]:
            return {
                "status": simulation.status,
                "personas_count": len(simulation.personas),
                "conversations_count": len(simulation.conversations)
            }
        
        # Calculate progress for each conversation
        conversation_stats = []
        active_count = 0
        completed_count = 0
        total_messages = 0
        
        for persona_id, conversation in simulation.conversations.items():
            # Find the persona
            persona = next((p for p in simulation.personas if p.id == persona_id), None)
            if not persona:
                continue
                
            # Get conversation stats
            message_count = len(conversation.messages)
            is_active = conversation.is_active
            progress_percentage = min(100, (message_count / (simulation.max_turns * 2)) * 100)
            
            # Count active and completed conversations
            if is_active:
                active_count += 1
            else:
                completed_count += 1
                
            total_messages += message_count
            
            conversation_stats.append({
                "persona_id": persona_id,
                "persona_name": persona.name,
                "message_count": message_count,
                "is_active": is_active,
                "progress_percentage": round(progress_percentage, 1),
                "has_summary": conversation.summary is not None
            })
        
        # Calculate overall progress
        total_conversations = len(simulation.conversations)
        overall_progress = 0
        if total_conversations > 0:
            overall_progress = (completed_count / total_conversations) * 100
        
        return {
            "status": simulation.status,
            "overall_progress": round(overall_progress, 1),
            "personas_count": len(simulation.personas),
            "conversations_count": total_conversations,
            "active_conversations": active_count,
            "completed_conversations": completed_count,
            "total_messages": total_messages,
            "conversation_stats": conversation_stats,
            "insights_count": len(simulation.aggregated_insights),
            "parallel_execution": True  # Flag to indicate conversations are running in parallel
        } 