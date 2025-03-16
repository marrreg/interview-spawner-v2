# Interview Spawner API Schema

This API powers an AI-driven customer interview simulation system. It allows you to create and manage simulations where AI personas act as potential customers, helping validate business ideas and gather customer insights.

## Base URL
```
http://localhost:5000/api
```

> **Note for Frontend Developers**: The default port is 5000, but on macOS you might need to use a different port (e.g., 5001) due to AirPlay using port 5000. Configure your frontend environment variables accordingly.

## Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

## Endpoints

### Simulations

The simulation is the core concept of the application. Each simulation represents a customer discovery session with multiple AI personas acting as potential customers.

#### List All Simulations
```http
GET /simulations
```

Use this endpoint to show a dashboard or overview of all running and completed simulations. Good for displaying a list/grid of simulations with their basic details.

**Response**
```json
{
    "simulations": [
        {
            "id": "string",                           // Unique identifier for the simulation
            "context": "string",                      // Business context/pitch provided
            "num_personas": "integer",                // Number of AI personas participating
            "max_turns": "integer",                   // Maximum conversation turns per persona
            "status": "string",                       // "pending", "running", "completed", or "stopped"
            "created_at": "string (ISO datetime)",    // When the simulation was created
            "updated_at": "string (ISO datetime)"     // Last update timestamp
        }
    ]
}
```

#### Create New Simulation
```http
POST /simulations
```

Entry point for starting a new customer discovery session. Use this when the user wants to validate a new business idea or product concept.

**Request Body**
```json
{
    "context": "string (required)",      // The business pitch or product description
    "num_personas": "integer (optional, default: 5)",   // How many AI customers to generate
    "max_turns": "integer (optional, default: 10)"      // Maximum back-and-forth messages per persona
}
```

**Response**
```json
{
    "simulation_id": "string",           // Use this ID for subsequent API calls
    "message": "string"                  // Success/status message
}
```

#### Get Simulation Details
```http
GET /simulations/{simulation_id}
```

Fetch detailed information about a specific simulation. Useful for the simulation detail view or status page.

**Response**
```json
{
    "id": "string",
    "context": "string",
    "num_personas": "integer",
    "max_turns": "integer",
    "status": "string",
    "created_at": "string (ISO datetime)",
    "updated_at": "string (ISO datetime)"
}
```

#### Start Simulation
```http
POST /simulations/{simulation_id}/start
```

Begins the simulation process. The system will start generating personas and initiating conversations.
Consider implementing a loading state in your UI when calling this endpoint.

**Response**
```json
{
    "message": "string"     // Success/failure message
}
```

#### Stop Simulation
```http
POST /simulations/{simulation_id}/stop
```

Halts an ongoing simulation. Useful for implementing a stop/pause button in your UI.

**Response**
```json
{
    "message": "string"     // Success/failure message
}
```

#### Get Simulation Personas
```http
GET /simulations/{simulation_id}/personas
```

Retrieves all AI personas generated for this simulation. Use this to display the list of interview participants
and their characteristics.

**Response**
```json
{
    "personas": [
        {
            "id": "string",              // Unique identifier for the persona
            "name": "string",            // Generated name
            "background": "string",      // Professional/personal background
            "goals": "array",            // Array of business/personal goals
            "pain_points": "array"       // Array of challenges/problems they face
        }
    ]
}
```

#### Get Simulation Conversations
```http
GET /simulations/{simulation_id}/conversations
```

Fetches all conversation threads between the system and AI personas. Perfect for implementing
a chat-like interface showing all interactions.

**Response**
```json
{
    "conversations": [
        {
            "id": "string",              // Unique conversation identifier
            "persona_id": "string",      // Links to a specific persona
            "messages": [
                {
                    "role": "string",    // "user" or "assistant"
                    "content": "string", // Message content
                    "timestamp": "string (ISO datetime)"
                }
            ]
        }
    ]
}
```

#### Get Simulation Insights
```http
GET /simulations/{simulation_id}/insights
```

Retrieves AI-generated insights from all conversations. Great for displaying a summary
or analysis dashboard of the customer discovery process.

**Response**
```json
{
    "insights": [
        {
            "theme": "string",           // Main insight category/theme
            "description": "string",     // Detailed explanation
            "evidence": "string",        // Supporting quotes/observations
            "impact": "string",          // Business impact assessment
            "confidence": "integer (1-5)" // Confidence score (1=low, 5=high)
        }
    ]
}
```

#### Get Simulation Progress
```http
GET /simulations/{simulation_id}/progress
```

Monitors the simulation's progress. Perfect for implementing progress bars or status indicators.

**Response**
```json
{
    "progress": {
        "total_turns": "integer",            // Total expected conversation turns
        "completed_turns": "integer",        // Completed conversation turns
        "status": "string",                  // Current simulation status
        "completion_percentage": "float"      // Progress as percentage (0-100)
    }
}
```

#### Delete Simulation
```http
DELETE /simulations/{simulation_id}
```

Removes a simulation and all associated data. Consider implementing a confirmation dialog
before calling this endpoint.

**Response**
```json
{
    "message": "string"     // Success/failure message
}
```

### Persona Generation

#### Reflect on Personas
```http
POST /reflect_personas
```

A utility endpoint that suggests potential customer personas based on your business context.
Useful for preview/planning before starting a full simulation.

**Request Body**
```json
{
    "context": "string (required)",              // Business/product description
    "num_personas": "integer (optional, default: 5)"   // Number of personas to generate
}
```

**Response**
```json
{
    "persona_outlines": [
        {
            "name": "string",            // Generated name
            "background": "string",      // Professional/personal background
            "goals": "array",            // Business/personal objectives
            "pain_points": "array"       // Challenges they face
        }
    ]
}
```

## Status Codes

The API uses the following standard HTTP status codes:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully (e.g., new simulation)
- `400 Bad Request`: Invalid request parameters (check your request body)
- `404 Not Found`: Resource not found (invalid simulation_id)
- `500 Internal Server Error`: Server error (retry later)

## Error Response Format

When an error occurs, the API will return a JSON object with the following structure:
Frontend developers should handle these errors appropriately and display user-friendly messages.

```json
{
    "error": "string (error message)"
}
```

## Rate Limiting

Currently, there are no rate limits implemented on the API endpoints. However, it's recommended
to implement reasonable polling intervals (e.g., 1-2 seconds) when checking simulation progress
or fetching updates.

## Versioning

The current API version is v1.0.0. The version can be checked using the status endpoint:

```http
GET /status
```

**Response**
```json
{
    "status": "string",     // "online" when system is operational
    "version": "string"     // Current API version
}
```

## Frontend Implementation Tips

1. **State Management**: Consider using a state management solution (Redux, MobX, etc.) to handle simulation data and progress.
2. **Real-time Updates**: Implement polling for the progress and conversations endpoints to show real-time updates.
3. **Error Handling**: Create a global error handling system to process API error responses consistently.
4. **Loading States**: Add loading indicators for all API calls, especially simulation creation and starting.
5. **Responsive Design**: The conversation interface should work well on both desktop and mobile devices.
6. **Caching**: Cache simulation results and conversations to improve performance and reduce API calls.

## Recommended Frontend Architecture

1. **Pages**:
   - Simulation List/Dashboard
   - Create Simulation Form
   - Simulation Detail View
   - Conversation Interface
   - Insights Dashboard

2. **Components**:
   - SimulationCard
   - PersonaList
   - ConversationThread
   - InsightCard
   - ProgressIndicator
   - ErrorBoundary

3. **Features**:
   - Real-time progress updates
   - Chat-like interface for conversations
   - Filterable/searchable insights
   - Export functionality for results
   - Responsive design for mobile use 