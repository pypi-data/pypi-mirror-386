/**
 * Dashboard Page Logic - v0.1.1
 * Populates service info, endpoints, and quick actions
 */
document.addEventListener('DOMContentLoaded', () => {
    // Service info
    const serviceInfo = document.getElementById('service-info');
    serviceInfo.innerHTML = `
        <div class="card-title">📋 Service Information</div>
        <div class="info-grid">
            <div class="info-item">
                <span class="info-label">Service Name:</span>
                <span class="info-value">MGraph-AI HTML Service</span>
            </div>
            <div class="info-item">
                <span class="info-label">Version:</span>
                <span class="info-value">v0.6.1</span>
            </div>
            <div class="info-item">
                <span class="info-label">Status:</span>
                <span class="info-value status-active">● Running</span>
            </div>
            <div class="info-item">
                <span class="info-label">Description:</span>
                <span class="info-value">Transform HTML documents using various operations including parsing, text extraction, and hash-based modifications</span>
            </div>
        </div>
    `;

    // Endpoints overview
    const endpointsOverview = document.getElementById('endpoints-overview');
    const endpoints = [
        {
            category: 'HTML Transformations',
            routes: [
                { route: 'POST /html/to__dict', desc: 'Parse HTML to dictionary structure' },
                { route: 'POST /html/to__text__nodes', desc: 'Extract text nodes with hash identifiers' },
                { route: 'POST /html/to__lines', desc: 'Format HTML as readable lines' },
                { route: 'POST /html/to__html__hashes', desc: 'Replace text with hashes (debugging)' },
                { route: 'POST /html/to__html__xxx', desc: 'Replace text with x\'s (privacy masking)' }
            ]
        },
        {
            category: 'Dictionary Operations',
            routes: [
                { route: 'POST /dict/to__html', desc: 'Reconstruct HTML from dictionary' },
                { route: 'POST /dict/to__text__nodes', desc: 'Extract text nodes from dictionary' },
                { route: 'POST /dict/to__lines', desc: 'Format dictionary as lines' }
            ]
        },
        {
            category: 'Hash Operations',
            routes: [
                { route: 'POST /hashes/to__html', desc: 'Apply hash mappings to reconstruct HTML' }
            ]
        }
    ];

    let endpointsHTML = '<div class="card-title">🔌 API Endpoints</div>';
    endpoints.forEach(group => {
        endpointsHTML += `<div class="endpoint-group">
            <h3>${group.category}</h3>
            <ul class="endpoint-list">`;
        group.routes.forEach(route => {
            endpointsHTML += `<li>
                <code class="route-name">${route.route}</code>
                <span class="route-desc">${route.desc}</span>
            </li>`;
        });
        endpointsHTML += '</ul></div>';
    });
    endpointsOverview.innerHTML = endpointsHTML;

    // Quick actions - NOW WITH WORKING PLAYGROUND LINK
    const quickActions = document.getElementById('quick-actions');
    quickActions.innerHTML = `
        <div class="card-title">⚡ Quick Actions</div>
        <div class="actions-grid">
            <a href="playground.html" class="action-card action-card-active">
                <div class="action-icon">🎮</div>
                <h3>Transformation Playground</h3>
                <p>Interactive testing of all endpoints</p>
                <span class="badge badge-success">Available Now!</span>
            </a>
            <div class="action-card coming-soon">
                <div class="action-icon">📊</div>
                <h3>Text Nodes Explorer</h3>
                <p>Deep dive into text extraction</p>
                <span class="badge">Coming Soon</span>
            </div>
            <div class="action-card coming-soon">
                <div class="action-icon">🔑</div>
                <h3>Hash Mapper</h3>
                <p>Semantic text modification workflow</p>
                <span class="badge">Coming Soon</span>
            </div>
        </div>
    `;
});
