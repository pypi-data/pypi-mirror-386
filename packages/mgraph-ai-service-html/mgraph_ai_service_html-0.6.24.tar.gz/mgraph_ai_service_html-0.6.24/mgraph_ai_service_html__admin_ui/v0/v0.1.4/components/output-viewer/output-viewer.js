/**
 * Output Viewer Component - v0.1.4
 *
 * FIXED: Uses output_type from endpoint configuration instead of auto-detection
 * ENHANCED: Uses Syntax__Highlighter service for reusable formatting
 *
 * Displays transformation results with proper formatting based on output type:
 * - json: Syntax-highlighted JSON with copy/download
 * - html: Syntax-highlighted HTML view
 * - text: Plain text display
 */

// Import syntax highlighter service at module load time
import { Syntax__Highlighter } from '../../../v0.1.4/js/utils/Syntax__Highlighter.js';

class Output__Viewer extends HTMLElement {
    constructor() {
        super();
        this.templateURL = '../v0.1.1/components/output-viewer/output-viewer.html';
        this.styleURL    = '../v0.1.1/components/output-viewer/output-viewer.css';
        this.state = {
            data: null,
            type: null
        };
    }

    async connectedCallback() {
        await this.loadStyles();
        await this.loadTemplate();
        this.attachEventListeners();

        // Inject syntax highlighting styles once
        Syntax__Highlighter.loadStyles();
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
        const copyBtn = this.querySelector('#copy-btn');
        const downloadBtn = this.querySelector('#download-btn');

        copyBtn.addEventListener('click', () => this.copyToClipboard());
        downloadBtn.addEventListener('click', () => this.downloadResult());
    }

    showLoading() {
        const content = this.querySelector('#output-content');
        content.innerHTML = `
            <div class="loading-state">
                <div class="spinner"></div>
                <p>Transforming...</p>
            </div>
        `;
        this.hideControls();
    }

    showError(error) {
        const content = this.querySelector('#output-content');
        content.innerHTML = `
            <div class="error-state">
                <h4>❌ Transformation Failed</h4>
                <p>${error.message || 'An unknown error occurred'}</p>
            </div>
        `;
        this.hideControls();
    }

    /**
     * Display transformation result - FIXED in v0.1.4
     * Uses Syntax__Highlighter service for all formatting
     * @param {*} data - The result from the API
     * @param {string} type - Type from endpoint config: 'json', 'html', or 'text'
     */
    showResult(data, type) {
        this.state.data = data;
        this.state.type = type;

        const content = this.querySelector('#output-content');

        // Use Syntax__Highlighter service
        const highlighted = Syntax__Highlighter.highlight(data, type);

        const cssClass = type === 'json' ? 'json-output' :
                        type === 'html' ? 'html-output' : 'text-output';

        content.innerHTML = `<pre class="${cssClass}">${highlighted}</pre>`;
        this.showControls();
    }

    showControls() {
        const controls = this.querySelector('.output-controls');
        controls.style.display = 'flex';
    }

    hideControls() {
        const controls = this.querySelector('.output-controls');
        controls.style.display = 'none';
    }

    async copyToClipboard() {
        const text = this.getRawOutput();
        try {
            await navigator.clipboard.writeText(text);
            alert('Copied to clipboard! ✅');
        } catch (error) {
            console.error('Failed to copy:', error);
            alert('Failed to copy to clipboard');
        }
    }

    downloadResult() {
        const text = this.getRawOutput();
        const type = this.state.type;

        let filename, mimeType;
        if (type === 'json') {
            filename = 'result.json';
            mimeType = 'application/json';
        } else if (type === 'html') {
            filename = 'result.html';
            mimeType = 'text/html';
        } else {
            filename = 'result.txt';
            mimeType = 'text/plain';
        }

        const blob = new Blob([text], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    getRawOutput() {
        if (this.state.type === 'json') {
            return JSON.stringify(this.state.data, null, 2);
        } else {
            return this.state.data;
        }
    }
}

customElements.define('output-viewer', Output__Viewer);