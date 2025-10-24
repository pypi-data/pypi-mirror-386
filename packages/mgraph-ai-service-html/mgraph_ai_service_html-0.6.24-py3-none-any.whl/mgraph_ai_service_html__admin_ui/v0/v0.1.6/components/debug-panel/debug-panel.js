/**
 * Debug Panel Component - v0.1.6
 * Quick testing controls
 * 
 * Emits:
 *   debug-action - { action: 'load-micro'|'load-simple'|'parse'|'rebuild'|'full-flow' }
 */

class DebugPanel extends HTMLElement {
    constructor() {
        super();
        console.log('🔧 DebugPanel constructor');
    }

    connectedCallback() {
        this.render();
        this.attachListeners();
        
        // Load CSS
        this.loadStyles();
    }

    loadStyles() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = '../v0.1.6/components/debug-panel/debug-panel.css';
        document.head.appendChild(link);
    }

    render() {
        this.innerHTML = `
            <div class="debug-panel">
                <div class="debug-panel-header">
                    🔧 Debug Controls
                </div>
                <div class="debug-panel-buttons">
                    <button class="btn-small btn-secondary" data-action="load-micro">
                        📝 Load Micro Sample
                    </button>
                    <button class="btn-small btn-secondary" data-action="load-simple">
                        📄 Load Simple Sample
                    </button>
                    <button class="btn-small btn-secondary" data-action="parse">
                        ▶️ Parse HTML
                    </button>
                    <button class="btn-small btn-secondary" data-action="rebuild">
                        🔄 Rebuild HTML
                    </button>
                    <button class="btn-small btn-danger" data-action="full-flow">
                        ⚡ Full Flow (Load→Parse→Rebuild)
                    </button>
                </div>
            </div>
        `;
    }

    attachListeners() {
        this.querySelectorAll('[data-action]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.currentTarget.dataset.action;
                console.log(`🔧 DebugPanel: Action ${action}`);
                
                this.dispatchEvent(new CustomEvent('debug-action', {
                    detail: { action },
                    bubbles: true
                }));
            });
        });
    }
}

customElements.define('debug-panel', DebugPanel);
console.log('✅ DebugPanel component registered');
