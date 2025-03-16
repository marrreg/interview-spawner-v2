from flask import Blueprint, request, jsonify
import json
from app.models.simulation_manager import SimulationManager
from app.models.persona_generator import PersonaGenerator

# Define blueprint
api_bp = Blueprint('api', __name__)

# Create a direct instance of SimulationManager
simulation_manager = SimulationManager()

@api_bp.route('/simulations', methods=['GET'])
def list_simulations():
    """List all simulations"""
    simulations = []
    for sim_id, simulation in simulation_manager.simulations.items():
        simulations.append(simulation.to_dict())
    
    return jsonify({'simulations': simulations}), 200

@api_bp.route('/simulations', methods=['POST'])
def create_simulation():
    """Create a new customer discovery simulation"""
    data = request.json
    
    if not data or 'context' not in data:
        return jsonify({'error': 'Context is required'}), 400
    
    # Extract parameters
    context = data['context']
    num_personas = data.get('num_personas', 5)
    max_turns = data.get('max_turns', 10)
    
    # Create a new simulation
    simulation_id = simulation_manager.create_simulation(
        context=context,
        num_personas=num_personas,
        max_turns=max_turns
    )
    
    return jsonify({
        'simulation_id': simulation_id,
        'message': 'Simulation created successfully'
    }), 201

@api_bp.route('/simulations/<simulation_id>', methods=['GET'])
def get_simulation(simulation_id):
    """Get simulation details and current status"""
    simulation = simulation_manager.get_simulation(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify(simulation.to_dict()), 200

@api_bp.route('/simulations/<simulation_id>/start', methods=['POST'])
def start_simulation(simulation_id):
    """Start the simulation"""
    success = simulation_manager.start_simulation(simulation_id)
    
    if not success:
        return jsonify({'error': 'Failed to start simulation'}), 400
    
    return jsonify({'message': 'Simulation started successfully'}), 200

@api_bp.route('/simulations/<simulation_id>/stop', methods=['POST'])
def stop_simulation(simulation_id):
    """Stop the simulation"""
    success = simulation_manager.stop_simulation(simulation_id)
    
    if not success:
        return jsonify({'error': 'Failed to stop simulation'}), 400
    
    return jsonify({'message': 'Simulation stopped successfully'}), 200

@api_bp.route('/simulations/<simulation_id>/personas', methods=['GET'])
def get_personas(simulation_id):
    """Get all personas for a simulation"""
    personas = simulation_manager.get_personas(simulation_id)
    
    if personas is None:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify({'personas': personas}), 200

@api_bp.route('/simulations/<simulation_id>/conversations', methods=['GET'])
def get_conversations(simulation_id):
    """Get all conversations for a simulation"""
    conversations = simulation_manager.get_conversations(simulation_id)
    
    if conversations is None:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify({'conversations': conversations}), 200

@api_bp.route('/simulations/<simulation_id>/insights', methods=['GET'])
def get_insights(simulation_id):
    """Get current insights from a simulation"""
    import logging
    logger = logging.getLogger('api')
    
    logger.info(f"Getting insights for simulation: {simulation_id}")
    insights = simulation_manager.get_insights(simulation_id)
    
    if insights is None:
        logger.warning(f"No simulation found with ID: {simulation_id}")
        return jsonify({'error': 'Simulation not found'}), 404
    
    # Validate insights before returning
    if not isinstance(insights, list):
        logger.error(f"Expected insights to be a list but got: {type(insights)}")
        insights = []
    
    # Make sure each insight has the required fields
    valid_insights = []
    for insight in insights:
        if not isinstance(insight, dict):
            logger.warning(f"Skipping non-dict insight: {insight}")
            continue
            
        # Ensure all required fields are present
        required_fields = ["theme", "description", "evidence", "impact", "confidence"]
        is_valid = True
        
        for field in required_fields:
            if field not in insight:
                logger.warning(f"Insight missing required field: {field}")
                is_valid = False
                break
        
        if is_valid:
            # Make sure no values are too long to prevent display issues
            for field in ["theme", "description", "evidence", "impact"]:
                if len(str(insight[field])) > 500:
                    logger.warning(f"Truncating long {field} value")
                    insight[field] = str(insight[field])[:497] + "..."
                    
            # Ensure confidence is a valid integer
            try:
                insight["confidence"] = int(insight["confidence"])
                if insight["confidence"] < 1 or insight["confidence"] > 5:
                    insight["confidence"] = max(1, min(5, insight["confidence"]))
            except (ValueError, TypeError):
                insight["confidence"] = 3  # Default to middle value
                
            valid_insights.append(insight)
    
    logger.info(f"Returning {len(valid_insights)} valid insights")
    return jsonify({'insights': valid_insights}), 200

@api_bp.route('/simulations/<simulation_id>/progress', methods=['GET'])
def get_progress(simulation_id):
    """Get the current progress of a simulation"""
    progress = simulation_manager.get_progress(simulation_id)
    
    if progress is None:
        return jsonify({'error': 'Simulation not found'}), 404
    
    return jsonify({'progress': progress}), 200

@api_bp.route('/simulations/<simulation_id>', methods=['DELETE'])
def delete_simulation(simulation_id):
    """Delete a simulation"""
    # Check if simulation exists
    simulation = simulation_manager.get_simulation(simulation_id)
    
    if not simulation:
        return jsonify({'error': 'Simulation not found'}), 404
    
    # Delete simulation from the simulation manager
    del simulation_manager.simulations[simulation_id]
    
    return jsonify({'message': 'Simulation deleted successfully'}), 200

@api_bp.route('/reflect_personas', methods=['POST'])
def reflect_personas():
    """Reflect on which personas would be best suited for the given context"""
    data = request.json
    
    if not data or 'context' not in data:
        return jsonify({'error': 'Context is required'}), 400
    
    # Extract parameters
    context = data['context']
    num_personas = data.get('num_personas', 5)
    
    # Create a persona generator instance
    persona_generator = PersonaGenerator()
    
    # Reflect on personas
    persona_outlines = persona_generator.reflect_on_personas(
        context=context,
        num_personas=num_personas
    )
    
    return jsonify({
        'persona_outlines': persona_outlines
    }), 200 