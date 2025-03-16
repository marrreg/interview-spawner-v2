/**
 * AI-Powered Customer Discovery Simulation
 * Main JavaScript file
 */

// Global variables
let currentSimulationId = null;
let pollingInterval = null;
let startTime = null;

// DOM ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize form submission
    const simulationForm = document.getElementById('simulation-form');
    if (simulationForm) {
        simulationForm.addEventListener('submit', createSimulation);
    }
    
    // Initialize simulation controls
    const startSimulationBtn = document.getElementById('start-simulation-btn');
    const stopSimulationBtn = document.getElementById('stop-simulation-btn');
    
    if (startSimulationBtn) {
        startSimulationBtn.addEventListener('click', startSimulation);
    }
    
    if (stopSimulationBtn) {
        stopSimulationBtn.addEventListener('click', stopSimulation);
    }
    
    // Check for existing simulations in localStorage
    checkExistingSimulations();
});

/**
 * Create a new simulation
 * @param {Event} e - Form submission event
 */
async function createSimulation(e) {
    e.preventDefault();
    
    // Get form values
    const context = document.getElementById('context').value.trim();
    const numPersonas = document.getElementById('num-personas').value;
    const maxTurns = document.getElementById('max-turns').value;
    
    // Validate
    if (!context) {
        showAlert('Please provide a context for the research.', 'danger');
        return;
    }
    
    // Show loading state
    const submitBtn = e.target.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Creating...';
    
    try {
        // Create simulation
        const response = await fetch('/api/simulations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                context: context,
                num_personas: parseInt(numPersonas),
                max_turns: parseInt(maxTurns)
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Store simulation ID
            currentSimulationId = data.simulation_id;
            
            // Store in localStorage
            saveSimulationToLocalStorage(data.simulation_id, context, numPersonas);
            
            // Show success message
            showAlert('Simulation created successfully!', 'success');
            
            // Reset form
            document.getElementById('context').value = '';
            
            // Update UI
            openSimulationDashboard(data.simulation_id);
            
            // Start polling for updates
            startPolling(data.simulation_id);
        } else {
            showAlert(`Error: ${data.error || 'Failed to create simulation'}`, 'danger');
        }
    } catch (error) {
        console.error('Error creating simulation:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    } finally {
        // Reset button
        submitBtn.disabled = false;
        submitBtn.textContent = originalBtnText;
    }
}

/**
 * Start the simulation
 */
async function startSimulation() {
    if (!currentSimulationId) return;
    
    try {
        const response = await fetch(`/api/simulations/${currentSimulationId}/start`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update UI
            document.getElementById('status-badge').textContent = 'Running';
            document.getElementById('status-badge').className = 'badge bg-success';
            
            // Start timer
            startTime = Date.now();
            
            // Disable start button, enable stop button
            document.getElementById('start-simulation-btn').disabled = true;
            document.getElementById('stop-simulation-btn').disabled = false;
            
            showAlert('Simulation started!', 'success');
        } else {
            showAlert(`Error: ${data.error || 'Failed to start simulation'}`, 'danger');
        }
    } catch (error) {
        console.error('Error starting simulation:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    }
}

/**
 * Stop the simulation
 */
async function stopSimulation() {
    if (!currentSimulationId) return;
    
    try {
        const response = await fetch(`/api/simulations/${currentSimulationId}/stop`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update UI
            document.getElementById('status-badge').textContent = 'Completed';
            document.getElementById('status-badge').className = 'badge bg-info';
            
            // Enable start button, disable stop button
            document.getElementById('start-simulation-btn').disabled = false;
            document.getElementById('stop-simulation-btn').disabled = true;
            
            showAlert('Simulation stopped!', 'info');
        } else {
            showAlert(`Error: ${data.error || 'Failed to stop simulation'}`, 'danger');
        }
    } catch (error) {
        console.error('Error stopping simulation:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    }
}

/**
 * Open the simulation dashboard
 * @param {string} simulationId - Simulation ID
 */
function openSimulationDashboard(simulationId) {
    // Set current simulation
    currentSimulationId = simulationId;
    
    // Show simulation modal
    const simulationModal = new bootstrap.Modal(document.getElementById('simulationModal'));
    simulationModal.show();
    
    // Load simulation data
    fetchSimulationData(simulationId);
}

/**
 * Start polling for simulation updates
 * @param {string} simulationId - Simulation ID
 */
function startPolling(simulationId) {
    // Clear any existing interval
    if (pollingInterval) {
        clearInterval(pollingInterval);
    }
    
    // Set up polling interval (every 2 seconds)
    pollingInterval = setInterval(() => {
        fetchSimulationData(simulationId);
    }, 2000);
    
    // Add event listener to stop polling when modal is closed
    document.getElementById('simulationModal').addEventListener('hidden.bs.modal', function () {
        stopPolling();
    });
}

/**
 * Stop polling for updates
 */
function stopPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

/**
 * Fetch simulation data
 * @param {string} simulationId - Simulation ID
 */
async function fetchSimulationData(simulationId) {
    try {
        // Get progress
        const progressResponse = await fetch(`/api/simulations/${simulationId}/progress`);
        const progressData = await progressResponse.json();
        
        if (progressResponse.ok) {
            updateProgressUI(progressData.progress);
        }
        
        // Get personas if in "ready" or later state
        if (progressData.progress.status !== 'created' && progressData.progress.status !== 'generating_personas') {
            const personasResponse = await fetch(`/api/simulations/${simulationId}/personas`);
            const personasData = await personasResponse.json();
            
            if (personasResponse.ok) {
                updatePersonasUI(personasData.personas);
            }
        }
        
        // Get conversations if in "running" or "completed" state
        if (progressData.progress.status === 'running' || progressData.progress.status === 'completed') {
            const conversationsResponse = await fetch(`/api/simulations/${simulationId}/conversations`);
            const conversationsData = await conversationsResponse.json();
            
            if (conversationsResponse.ok) {
                updateConversationsUI(conversationsData.conversations);
            }
            
            // Get insights
            const insightsResponse = await fetch(`/api/simulations/${simulationId}/insights`);
            const insightsData = await insightsResponse.json();
            
            if (insightsResponse.ok) {
                updateInsightsUI(insightsData.insights);
            }
        }
        
        // If simulation is completed, stop polling
        if (progressData.progress.status === 'completed' || progressData.progress.status === 'error') {
            stopPolling();
        }
        
    } catch (error) {
        console.error('Error fetching simulation data:', error);
    }
}

/**
 * Update Progress UI
 * @param {Object} progress - Simulation progress data
 */
function updateProgressUI(progress) {
    const statusDisplay = document.getElementById('simulation-status');
    const statusBadge = document.getElementById('status-badge');
    
    // Update status display
    let statusText = progress.status.charAt(0).toUpperCase() + progress.status.slice(1).replace('_', ' ');
    let badgeClass = 'bg-secondary';
    
    if (progress.status === 'running') {
        statusText = 'Running';
        badgeClass = 'bg-success';
    } else if (progress.status === 'completed') {
        statusText = 'Completed';
        badgeClass = 'bg-primary';
    } else if (progress.status === 'error') {
        statusText = 'Error';
        badgeClass = 'bg-danger';
    } else if (progress.status === 'generating_personas') {
        statusText = 'Generating Personas';
        badgeClass = 'bg-warning text-dark';
    } else if (progress.status === 'ready') {
        statusText = 'Ready to Start';
        badgeClass = 'bg-info text-dark';
    }
    
    statusDisplay.textContent = statusText;
    statusBadge.className = `badge ${badgeClass}`;
    
    // Update metrics
    document.getElementById('personas-count').textContent = progress.personas_count || 0;
    document.getElementById('conversations-count').textContent = progress.conversations_count || 0;
    document.getElementById('messages-count').textContent = progress.total_messages || 0;
    
    // Show parallel execution indicator if available
    const parallelExecutionIndicator = document.getElementById('parallel-execution-indicator');
    if (parallelExecutionIndicator) {
        if (progress.parallel_execution) {
            parallelExecutionIndicator.style.display = 'inline-block';
        } else {
            parallelExecutionIndicator.style.display = 'none';
        }
    }
    
    // Update active conversations indicator
    const activeConversationsIndicator = document.getElementById('active-conversations');
    if (activeConversationsIndicator) {
        const container = document.getElementById('active-conversations-container');
        if (progress.active_conversations) {
            activeConversationsIndicator.textContent = progress.active_conversations;
            container.style.display = 'inline-block';
        } else {
            container.style.display = 'none';
        }
    }
    
    // Update progress bar
    let progressPercentage = 0;
    
    if (progress.status === 'generating_personas') {
        progressPercentage = 10;
    } else if (progress.status === 'ready') {
        progressPercentage = 20;
    } else if (progress.status === 'running') {
        if (progress.overall_progress !== undefined) {
            // Use the server-calculated progress if available
            progressPercentage = 20 + (progress.overall_progress * 0.8); // Scale to 20-100%
        } else {
            // Calculate based on messages compared to expected total
            const expectedTotal = progress.conversations_count * 2 * 10; // assuming 10 turns per conversation
            progressPercentage = 20 + ((progress.total_messages / expectedTotal) * 80);
        }
    } else if (progress.status === 'completed') {
        progressPercentage = 100;
    }
    
    document.getElementById('simulation-progress-bar').style.width = `${Math.min(progressPercentage, 100)}%`;
    
    // Update elapsed time
    if (progress.start_time) {
        startTime = progress.start_time * 1000; // convert to milliseconds
        updateElapsedTime();
    }
    
    // Update buttons
    if (progress.status === 'ready') {
        document.getElementById('start-simulation-btn').disabled = false;
        document.getElementById('stop-simulation-btn').disabled = true;
    } else if (progress.status === 'running') {
        document.getElementById('start-simulation-btn').disabled = true;
        document.getElementById('stop-simulation-btn').disabled = false;
    } else {
        document.getElementById('start-simulation-btn').disabled = true;
        document.getElementById('stop-simulation-btn').disabled = true;
    }
}

/**
 * Update Personas UI
 * @param {Array} personas - List of personas
 */
function updatePersonasUI(personas) {
    const personasContainer = document.getElementById('personas-container');
    
    // Clear existing content
    personasContainer.innerHTML = '';
    
    if (personas.length === 0) {
        personasContainer.innerHTML = '<p class="text-center text-muted">No personas available</p>';
        return;
    }
    
    // Add personas
    personas.forEach(persona => {
        const personaCard = document.createElement('div');
        personaCard.className = 'col-md-4 mb-4';
        
        // Get initials for avatar
        const initials = persona.name.split(' ').map(n => n[0]).join('').toUpperCase();
        
        personaCard.innerHTML = `
            <div class="card persona-card h-100">
                <div class="card-body text-center">
                    <div class="persona-avatar">${initials}</div>
                    <h5 class="card-title">${persona.name}</h5>
                    <p class="card-text text-muted">${persona.age} | ${persona.occupation}</p>
                    <p class="card-text">${persona.location}</p>
                    <hr>
                    <div class="text-start">
                        <small class="d-block mb-1"><strong>Goals:</strong> ${persona.goals.slice(0, 2).join(', ')}</small>
                        <small class="d-block mb-1"><strong>Pain Points:</strong> ${persona.pain_points.slice(0, 2).join(', ')}</small>
                        <small class="d-block"><strong>Motivations:</strong> ${persona.motivations.slice(0, 2).join(', ')}</small>
                    </div>
                </div>
                <div class="card-footer bg-white">
                    <button class="btn btn-sm btn-outline-primary w-100" data-bs-toggle="collapse" data-bs-target="#persona-details-${persona.id}">
                        View Details
                    </button>
                    <div class="collapse mt-3" id="persona-details-${persona.id}">
                        <p class="small">${persona.description}</p>
                        <hr>
                        <p class="small"><strong>Background:</strong> ${persona.background}</p>
                    </div>
                </div>
            </div>
        `;
        
        personasContainer.appendChild(personaCard);
    });
}

/**
 * Update Conversations UI
 * @param {Array} conversations - List of conversations
 */
function updateConversationsUI(conversations) {
    const conversationsContainer = document.getElementById('conversations-container');
    
    // Clear existing content
    conversationsContainer.innerHTML = '';
    
    if (conversations.length === 0) {
        conversationsContainer.innerHTML = '<p class="text-center text-muted">No conversations available</p>';
        return;
    }
    
    // Create accordion for conversations
    const accordion = document.createElement('div');
    accordion.className = 'accordion';
    accordion.id = 'conversationsAccordion';
    
    // Add conversations
    conversations.forEach((conversation, index) => {
        const accordionItem = document.createElement('div');
        accordionItem.className = 'accordion-item';
        
        // Find corresponding persona
        const personaId = conversation.persona_id;
        
        // Fix: Get the actual message count from the array length
        const messageCount = Array.isArray(conversation.messages) ? conversation.messages.length : 0;
        const messageText = messageCount === 1 ? 'message' : 'messages';
        
        accordionItem.innerHTML = `
            <h2 class="accordion-header">
                <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#conversation-${conversation.id}">
                    Conversation with Persona #${personaId.substring(0, 6)}... (${messageCount} ${messageText})
                </button>
            </h2>
            <div id="conversation-${conversation.id}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" data-bs-parent="#conversationsAccordion">
                <div class="accordion-body p-0">
                    <div class="conversation-container d-flex flex-column">
                        ${Array.isArray(conversation.messages) ? conversation.messages.map(msg => `
                            <div class="message ${msg.role}">
                                <strong>${msg.role.charAt(0).toUpperCase() + msg.role.slice(1)}:</strong>
                                <div>${msg.content}</div>
                                <small class="text-muted">${new Date(msg.timestamp * 1000).toLocaleTimeString()}</small>
                            </div>
                        `).join('') : '<div class="p-3">No messages available</div>'}
                    </div>
                    ${conversation.summary ? `
                        <div class="p-3 border-top">
                            <h6>Conversation Summary:</h6>
                            <p>${conversation.summary}</p>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
        
        accordion.appendChild(accordionItem);
    });
    
    conversationsContainer.appendChild(accordion);
}

/**
 * Update Insights UI
 * @param {Array} insights - List of insights
 */
function updateInsightsUI(insights) {
    const insightsContainer = document.getElementById('insights-container');
    
    // Clear placeholder
    if (insightsContainer.querySelector('p.text-muted')) {
        insightsContainer.innerHTML = '';
    }
    
    if (!insights || insights.length === 0) {
        if (insightsContainer.children.length === 0) {
            insightsContainer.innerHTML = '<p class="text-center text-muted">No insights available yet</p>';
        }
        return;
    }
    
    // Check if insights already exist (by comparing first insight)
    if (insightsContainer.querySelector('.insight-card')) {
        const firstInsightTheme = insightsContainer.querySelector('.insight-card h5').textContent;
        if (insights[0].theme === firstInsightTheme) {
            // Insights haven't changed, no need to update
            return;
        }
    }
    
    // Clear existing content
    insightsContainer.innerHTML = '';
    
    // Add insights
    insights.forEach(insight => {
        const cardDiv = createInsightCard(insight);
        insightsContainer.appendChild(cardDiv);
    });
}

function createInsightCard(insight) {
    // Create confidence dots
    let confidenceDotsHTML = '';
    for (let i = 1; i <= 5; i++) {
        confidenceDotsHTML += `<div class="confidence-dot ${i <= insight.confidence ? 'filled' : ''}"></div>`;
    }
    
    // Create a card element
    const cardDiv = document.createElement('div');
    cardDiv.className = 'insight-card';
    
    // Set the HTML content of the card
    cardDiv.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <h5 class="insight-title fw-bold mb-0">${insight.title || insight.theme}</h5>
            <div class="insight-confidence">
                <div class="confidence-meter">${confidenceDotsHTML}</div>
            </div>
        </div>
        <p class="insight-text">${insight.content || insight.description}</p>
        ${insight.suggestions ? `
        <div class="insight-recommendations mt-2">
            <span class="text-primary"><i class="bi bi-lightbulb me-1"></i> Recommendation:</span>
            <div class="mt-1 ps-2 text-gray-700 border-start border-2" style="border-color: var(--accent-color) !important; font-size: 0.92rem;">
                ${insight.suggestions}
            </div>
        </div>` : ''}
        <div class="insight-footer d-flex justify-content-between align-items-center">
            <div>
                <span class="badge bg-light text-primary">
                    <i class="bi bi-tag-fill me-1"></i>${insight.category || insight.impact || 'General'}
                </span>
                ${insight.source ? `<span class="badge ms-1 bg-light text-secondary">
                    <i class="bi bi-chat-square-text me-1"></i>${insight.source}
                </span>` : ''}
            </div>
            <span class="text-muted small">
                <i class="bi bi-chat-quote me-1"></i>${insight.source_count || insight.evidence || 'customer interviews'}
            </span>
        </div>
    `;
    
    return cardDiv;
}

/**
 * Update elapsed time
 */
function updateElapsedTime() {
    if (!startTime) return;
    
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    document.getElementById('elapsed-time').textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
    
    // Update every second
    requestAnimationFrame(updateElapsedTime);
}

/**
 * Save simulation to localStorage
 * @param {string} id - Simulation ID
 * @param {string} context - Research context
 * @param {number} numPersonas - Number of personas
 */
function saveSimulationToLocalStorage(id, context, numPersonas) {
    // Get existing simulations
    let simulations = JSON.parse(localStorage.getItem('customerDiscoverySimulations') || '[]');
    
    // Add new simulation
    simulations.push({
        id: id,
        context: context,
        numPersonas: numPersonas,
        createdAt: Date.now()
    });
    
    // Store in localStorage
    localStorage.setItem('customerDiscoverySimulations', JSON.stringify(simulations));
    
    // Update UI
    displayExistingSimulations(simulations);
}

/**
 * Check for existing simulations in localStorage
 */
function checkExistingSimulations() {
    const simulations = JSON.parse(localStorage.getItem('customerDiscoverySimulations') || '[]');
    
    if (simulations.length > 0) {
        displayExistingSimulations(simulations);
    }
}

/**
 * Display existing simulations
 * @param {Array} simulations - List of simulations
 */
function displayExistingSimulations(simulations) {
    const simulationsContainer = document.getElementById('simulations-container');
    const tableBody = document.getElementById('simulations-table-body');
    
    if (!simulationsContainer || !tableBody) return;
    
    // Show container
    simulationsContainer.classList.remove('d-none');
    
    // Clear table
    tableBody.innerHTML = '';
    
    // Add simulations
    simulations.forEach(simulation => {
        const row = document.createElement('tr');
        
        // Format date
        const date = new Date(simulation.createdAt);
        const formattedDate = `${date.toLocaleDateString()} ${date.toLocaleTimeString()}`;
        
        row.innerHTML = `
            <td>${simulation.id.substring(0, 8)}...</td>
            <td>${simulation.context.substring(0, 50)}${simulation.context.length > 50 ? '...' : ''}</td>
            <td>${simulation.numPersonas}</td>
            <td><span class="badge bg-secondary status-badge" data-simulation-id="${simulation.id}">Unknown</span></td>
            <td>
                <div class="progress">
                    <div class="progress-bar progress-progress-bar" role="progressbar" style="width: 0%" data-simulation-id="${simulation.id}"></div>
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-primary open-simulation-btn" data-simulation-id="${simulation.id}">Open</button>
                <button class="btn btn-sm btn-danger delete-simulation-btn" data-simulation-id="${simulation.id}">Delete</button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Add event listeners to buttons
    document.querySelectorAll('.open-simulation-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const simulationId = this.getAttribute('data-simulation-id');
            openSimulationDashboard(simulationId);
        });
    });
    
    // Add event listeners to delete buttons
    document.querySelectorAll('.delete-simulation-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const simulationId = this.getAttribute('data-simulation-id');
            if (confirm('Are you sure you want to delete this simulation? This action cannot be undone.')) {
                deleteSimulation(simulationId);
            }
        });
    });
    
    // Fetch status for each simulation
    simulations.forEach(simulation => {
        fetchSimulationStatus(simulation.id);
    });
}

/**
 * Fetch status for a simulation
 * @param {string} simulationId - Simulation ID
 */
async function fetchSimulationStatus(simulationId) {
    try {
        const response = await fetch(`/api/simulations/${simulationId}/progress`);
        
        if (response.ok) {
            const data = await response.json();
            
            // Update status badge
            const statusBadge = document.querySelector(`.status-badge[data-simulation-id="${simulationId}"]`);
            if (statusBadge) {
                statusBadge.textContent = data.progress.status.charAt(0).toUpperCase() + data.progress.status.slice(1);
                
                // Set badge color
                let badgeClass = 'bg-secondary';
                switch (data.progress.status) {
                    case 'generating_personas':
                        badgeClass = 'bg-warning';
                        break;
                    case 'ready':
                        badgeClass = 'bg-primary';
                        break;
                    case 'running':
                        badgeClass = 'bg-success';
                        break;
                    case 'completed':
                        badgeClass = 'bg-info';
                        break;
                    case 'error':
                        badgeClass = 'bg-danger';
                        break;
                }
                statusBadge.className = `badge ${badgeClass} status-badge`;
            }
            
            // Update progress bar
            const progressBar = document.querySelector(`.progress-progress-bar[data-simulation-id="${simulationId}"]`);
            if (progressBar) {
                let progressPercentage = 0;
                
                if (data.progress.status === 'generating_personas') {
                    progressPercentage = 10;
                } else if (data.progress.status === 'ready') {
                    progressPercentage = 20;
                } else if (data.progress.status === 'running') {
                    const expectedTotal = data.progress.total_conversations * 2 * 10;
                    progressPercentage = 20 + (data.progress.total_messages / expectedTotal) * 80;
                } else if (data.progress.status === 'completed') {
                    progressPercentage = 100;
                }
                
                progressBar.style.width = `${Math.min(progressPercentage, 100)}%`;
            }
        }
    } catch (error) {
        console.error('Error fetching simulation status:', error);
    }
}

/**
 * Show an alert message
 * @param {string} message - Alert message
 * @param {string} type - Alert type (success, info, warning, danger)
 */
function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to page
    const container = document.querySelector('.container');
    container.insertBefore(alert, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Delete a simulation
 * @param {string} simulationId - Simulation ID
 */
async function deleteSimulation(simulationId) {
    try {
        const response = await fetch(`/api/simulations/${simulationId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Remove from localStorage
            let simulations = JSON.parse(localStorage.getItem('customerDiscoverySimulations') || '[]');
            simulations = simulations.filter(sim => sim.id !== simulationId);
            localStorage.setItem('customerDiscoverySimulations', JSON.stringify(simulations));
            
            // Update UI
            displayExistingSimulations(simulations);
            
            // Show success message
            showAlert('Simulation deleted successfully!', 'success');
            
            // If the current simulation is the one being deleted, clear it
            if (currentSimulationId === simulationId) {
                currentSimulationId = null;
                stopPolling();
                
                // Close modal if open
                const simulationModal = document.getElementById('simulationModal');
                if (simulationModal && simulationModal.classList.contains('show')) {
                    const bsModal = bootstrap.Modal.getInstance(simulationModal);
                    if (bsModal) {
                        bsModal.hide();
                    }
                }
            }
        } else {
            showAlert(`Error: ${data.error || 'Failed to delete simulation'}`, 'danger');
        }
    } catch (error) {
        console.error('Error deleting simulation:', error);
        showAlert('An error occurred. Please try again.', 'danger');
    }
} 