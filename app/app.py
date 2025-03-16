import os
import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import internal modules
from app.api.routes import api_bp
from app.models.simulation_manager import SimulationManager

# Create Flask app
app = Flask(__name__)
CORS(app)

# Configure app
app.config.from_mapping(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key'),
    ANTHROPIC_API_KEY=os.environ.get('ANTHROPIC_API_KEY'),
    OPENAI_API_KEY=os.environ.get('OPENAI_API_KEY'),
)

# Create simulation manager
simulation_manager = SimulationManager()

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    """Render the main application page"""
    return render_template('index.html', now=datetime.datetime.now())

@app.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html', now=datetime.datetime.now())

@app.route('/status')
def status():
    """Return API status"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0'
    })

# Context processor for all templates
@app.context_processor
def inject_now():
    return {'now': datetime.datetime.now()}

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', '0') == '1', host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 