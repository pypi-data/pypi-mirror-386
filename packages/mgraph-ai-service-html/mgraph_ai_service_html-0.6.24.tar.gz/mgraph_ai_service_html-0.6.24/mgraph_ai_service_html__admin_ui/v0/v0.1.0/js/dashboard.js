/**
 * Dashboard Page Logic
 * v0.1.0
 * 
 * Handles dashboard initialization, endpoint display, and sample loading.
 */

document.addEventListener('DOMContentLoaded', () => {
    initializeDashboard();
});

/**
 * Initialize dashboard page
 */
function initializeDashboard() {
    displayEndpoints();
    setupSampleCards();
    updateStats();
}

/**
 * Display available API endpoints grouped by category
 */
function displayEndpoints() {
    const endpoints = window.apiClient.getAllEndpoints();
    const container = document.getElementById('endpoints-container');
    
    if (!container) return;
    
    let html = '<div class="endpoint-list">';
    
    // HTML Routes
    html += createEndpointGroup('HTML Transformations', endpoints.html, 'Process HTML input directly');
    
    // Dict Routes
    html += createEndpointGroup('Dictionary Operations', endpoints.dict, 'Process parsed HTML dictionaries');
    
    // Hashes Routes
    html += createEndpointGroup('Hash Operations', endpoints.hashes, 'Apply text modifications using hash mappings');
    
    html += '</div>';
    
    container.innerHTML = html;
}

/**
 * Create endpoint group HTML
 */
function createEndpointGroup(title, endpoints, description) {
    let html = '<div class="endpoint-group">';
    html += `<div class="endpoint-group-header">
                <strong>${title}</strong>
                ${description ? `<div style="font-weight:normal; font-size:0.875rem; color:var(--text-secondary); margin-top:4px;">${description}</div>` : ''}
             </div>`;
    
    for (const [key, endpoint] of Object.entries(endpoints)) {
        html += `
            <div class="endpoint-item">
                <div class="endpoint-info">
                    <div>
                        <span class="endpoint-method ${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                        <code class="endpoint-path">${endpoint.path}</code>
                    </div>
                    <div class="endpoint-description">${endpoint.description}</div>
                </div>
                <div class="endpoint-actions">
                    <button class="btn btn-sm btn-secondary" onclick="copyEndpoint('${endpoint.path}')">
                        📋 Copy Path
                    </button>
                </div>
            </div>
        `;
    }
    
    html += '</div>';
    return html;
}

/**
 * Copy endpoint path to clipboard
 */
function copyEndpoint(path) {
    navigator.clipboard.writeText(path).then(() => {
        showToast('Endpoint path copied to clipboard!', 'success');
    }).catch(err => {
        console.error('Failed to copy:', err);
        showToast('Failed to copy endpoint path', 'error');
    });
}

/**
 * Setup sample card event handlers
 */
function setupSampleCards() {
    const sampleCards = document.querySelectorAll('.sample-card');
    
    sampleCards.forEach(card => {
        const viewBtn = card.querySelector('.view-sample-btn');
        if (viewBtn) {
            viewBtn.addEventListener('click', (e) => {
                const samplePath = e.target.dataset.samplePath;
                viewSample(samplePath);
            });
        }
    });
}

/**
 * View sample HTML in new window
 */
function viewSample(samplePath) {
    window.open(samplePath, '_blank');
}

/**
 * Update dashboard statistics
 */
function updateStats() {
    const endpoints = window.apiClient.getAllEndpoints();
    
    // Count total endpoints
    let totalEndpoints = 0;
    for (const category in endpoints) {
        totalEndpoints += Object.keys(endpoints[category]).length;
    }
    
    // Update stats display
    updateStatValue('total-endpoints', totalEndpoints);
    updateStatValue('endpoint-categories', Object.keys(endpoints).length);
    updateStatValue('sample-files', 3); // simple, complex, dashboard
}

/**
 * Update stat value in DOM
 */
function updateStatValue(id, value) {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.position = 'fixed';
    toast.style.top = '20px';
    toast.style.right = '20px';
    toast.style.zIndex = '9999';
    toast.style.minWidth = '300px';
    toast.style.animation = 'slideIn 0.3s ease-out';
    toast.textContent = message;
    
    // Add to DOM
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

/**
 * Navigate to playground (will be available in v0.1.1)
 */
function navigateToPlayground() {
    // Check if playground exists
    fetch('/html-service/v0/v0.1.1/playground.html', { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                window.location.href = '/html-service/v0/v0.1.1/playground.html';
            } else {
                showToast('Playground not available yet. Coming in v0.1.1!', 'info');
            }
        })
        .catch(() => {
            showToast('Playground not available yet. Coming in v0.1.1!', 'info');
        });
}

// Add CSS animations for toast
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
