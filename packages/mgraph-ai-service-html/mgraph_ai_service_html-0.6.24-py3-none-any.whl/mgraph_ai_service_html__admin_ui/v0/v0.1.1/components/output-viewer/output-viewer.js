/**
 * Output Viewer Component
 * Displays transformation results with appropriate formatting
 */
class OutputViewer extends HTMLElement {
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

    showResult(data, type) {
        this.state.data = data;
        this.state.type = type;

        const content = this.querySelector('#output-content');
        
        if (type === 'json') {
            content.innerHTML = `<pre class="json-output">${this.formatJSON(data)}</pre>`;
        } else if (type === 'html') {
            content.innerHTML = `<pre class="html-output">${this.escapeHtml(data)}</pre>`;
        } else if (type === 'text') {
            content.innerHTML = `<pre class="text-output">${this.escapeHtml(data)}</pre>`;
        }

        this.showControls();
    }

    formatJSON(obj) {
        return JSON.stringify(obj, null, 2)
            .replace(/"([^"]+)":/g, '<span class="json-key">"$1"</span>:')
            .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
            .replace(/: (\d+)/g, ': <span class="json-number">$1</span>')
            .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
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

customElements.define('output-viewer', OutputViewer);
