/**
 * Transformation Selector Component
 * Allows user to select endpoint and configure parameters
 */
class TransformationSelector extends HTMLElement {
    constructor() {
        super();
        this.templateURL = '../v0.1.1/components/transformation-selector/transformation-selector.html';
        this.styleURL    = '../v0.1.1/components/transformation-selector/transformation-selector.css';
        
        // Endpoint definitions
        this.endpoints = {
            'html-to-dict': {
                route: '/html/to/dict',
                description: 'Parse HTML into a nested dictionary structure representing the DOM tree',
                method: 'POST',
                requiresMaxDepth: false,
                inputType: 'html'
            },
            'html-to-text-nodes': {
                route: '/html/to/text/nodes',
                description: 'Extract all text nodes with unique hash identifiers for semantic modification',
                method: 'POST',
                requiresMaxDepth: true,
                inputType: 'html'
            },
            'html-to-tree-view': {
                route: '/html/to/tree/view',
                description: 'Format HTML as readable indented tree view showing structure',
                method: 'POST',
                requiresMaxDepth: false,
                inputType: 'html'
            },
            'html-to-html-hashes': {
                route: '/html/to/html/hashes',
                description: 'Replace all text content with hash identifiers (debugging visualization)',
                method: 'POST',
                requiresMaxDepth: true,
                inputType: 'html'
            },
            'html-to-html-xxx': {
                route: '/html/to/html/xxx',
                description: 'Replace all text content with x\'s (privacy masking visualization)',
                method: 'POST',
                requiresMaxDepth: true,
                inputType: 'html'
            },
            'dict-to-html': {
                route: '/dict/to/html',
                description: 'Reconstruct HTML from dictionary structure',
                method: 'POST',
                requiresMaxDepth: false,
                inputType: 'dict'
            },
            'dict-to-text-nodes': {
                route: '/dict/to/text/nodes',
                description: 'Extract text nodes from dictionary structure',
                method: 'POST',
                requiresMaxDepth: true,
                inputType: 'dict'
            },
            'dict-to-tree-view': {
                route: '/dict/to/tree/view',
                description: 'Format dictionary as readable  tree view',
                method: 'POST',
                requiresMaxDepth: false,
                inputType: 'dict'
            },
            'hashes-to-html': {
                route: '/hashes/to/html',
                description: 'Apply hash mappings to reconstruct HTML with modified text',
                method: 'POST',
                requiresMaxDepth: false,
                inputType: 'hashes'
            }
        };
    }

    async connectedCallback() {
        await this.loadStyles();
        await this.loadTemplate();
        this.attachEventListeners();
    }

    async loadStyles() {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = this.styleURL;
        document.head.appendChild(link);
    }

    async loadTemplate() {
        const response = await fetch(this.templateURL);
        const html = await response.text();
        this.innerHTML = html;
    }

    attachEventListeners() {
        const selector = this.querySelector('#endpoint-selector');
        const transformBtn = this.querySelector('#transform-btn');
        const maxDepthSlider = this.querySelector('#max-depth-slider');
        const maxDepthValue = this.querySelector('#max-depth-value');

        // Endpoint selection
        selector.addEventListener('change', (e) => {
            const endpointId = e.target.value;
            if (endpointId) {
                this.showEndpointInfo(endpointId);
                transformBtn.disabled = false;
            } else {
                this.hideEndpointInfo();
                transformBtn.disabled = true;
            }
        });

        // Max depth slider
        maxDepthSlider.addEventListener('input', (e) => {
            maxDepthValue.textContent = e.target.value;
        });

        // Transform button
        transformBtn.addEventListener('click', () => {
            this.handleTransform();
        });
    }

    showEndpointInfo(endpointId) {
        const endpoint    = this.endpoints[endpointId];
        const infoDiv     = this.querySelector('#endpoint-info');
        const descSpan    = this.querySelector('#endpoint-description');
        const configPanel = this.querySelector('#config-panel');

        descSpan.textContent = endpoint.description;
        infoDiv.style.display = 'block';

        // Show config panel if max_depth is needed
        if (endpoint.requiresMaxDepth) {
            configPanel.style.display = 'block';
        } else {
            configPanel.style.display = 'none';
        }
    }

    hideEndpointInfo() {
        const infoDiv = this.querySelector('#endpoint-info');
        const configPanel = this.querySelector('#config-panel');
        infoDiv.style.display = 'none';
        configPanel.style.display = 'none';
    }

    handleTransform() {
        const selector = this.querySelector('#endpoint-selector');
        const endpointId = selector.value;
        const endpoint = this.endpoints[endpointId];
        
        const config = {
            endpointId,
            route: endpoint.route,
            inputType: endpoint.inputType
        };

        // Add max_depth if required
        if (endpoint.requiresMaxDepth) {
            const maxDepthSlider = this.querySelector('#max-depth-slider');
            config.maxDepth = parseInt(maxDepthSlider.value);
        }

        this.emit('transformation-requested', config);
    }

    emit(eventName, detail) {
        this.dispatchEvent(new CustomEvent(eventName, { 
            detail, 
            bubbles: true 
        }));
    }
}

customElements.define('transformation-selector', TransformationSelector);
