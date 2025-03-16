# AI-Powered Customer Discovery Simulation

An application that optimizes customer research by simulating realistic, parallel AI-driven interviews to uncover customer pain points and critical insights without direct human involvement.

## Features

- **User Input**: Define research context, industry, domain, or problem statement
- **Persona Generation**: Create diverse, realistic customer personas
- **Parallel AI Interviews**: Run multiple simultaneous AI-driven conversations
- **Real-time Insights**: Extract and display themes, pain points, and opportunities
- **Progress Tracking**: Monitor individual and aggregated conversation progress

## Technical Architecture

- **Backend**: Python/Flask API
- **Frontend**: HTML/CSS/JavaScript with modern UI
- **AI Integration**: 
  - Claude 3.7 Sonnet for advanced persona creation
  - Claude 3.5 (or equivalent) for conversation management
  - Real-time insight aggregation

## Getting Started

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up your environment:
   ```
   cp .env.example .env
   ```
   Update the `.env` file with your API keys
   
4. Run the application:
   ```
   python -m app.app
   ```
   
5. Open your browser to `http://localhost:5000`

## License

MIT 