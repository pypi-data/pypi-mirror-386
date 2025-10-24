/**
 * Column Created Component - v0.1.6
 * Created HTML output with Copy/Download
 * 
 * Emits:
 *   rebuild-requested - {}
 *   copy-requested - {}
 *   download-requested - {}
 */

import { Syntax__Highlighter } from '../../../v0.1.4/js/utils/Syntax__Highlighter.js';

class ColumnCreated extends HTMLElement {
    constructor() {
        super();
        console.log('✨ ColumnCreated constructor');
        this.mode = 'view'; // 'view' only for now (preview in v0.1.7)
        this.createdHtml = '';
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
        link.href = '../v0.1.6/components/column-created/column-created.css';
        document.head.appendChild(link);
    }

    render() {
        this.innerHTML = `
            <div class="column" id="column-created" data-mode="${this.mode}">
                <div class="column-header">
                    <h2>✨ Created HTML</h2>

                    

                    <div class="column-actions">
                        <button class="btn-small btn-primary" id="btn-transform-rebuild">
                            ▶ Rebuild
                        </button>
                        <button class="btn-small btn-secondary" id="btn-copy-output">Copy</button>
                        <button class="btn-small btn-secondary" id="btn-download-output">Download</button>
                    </div>
                </div>

                <div class="column-content">
                    <!-- VIEW MODE (only mode for now) -->
                    <div class="column-mode column-mode-view">
                        <div class="output-area">
                            <div class="output-content" id="created-html-output">
                                <div class="empty-state">
                                    <div class="empty-state-icon">✨</div>
                                    <div class="empty-state-text">Rebuilt HTML will appear here after reconstruction</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    attachListeners() {
        // Rebuild button
        const rebuildBtn = this.querySelector('#btn-transform-rebuild');
        rebuildBtn?.addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('rebuild-requested', {
                bubbles: true
            }));
        });

        // Copy button
        const copyBtn = this.querySelector('#btn-copy-output');
        copyBtn?.addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('copy-requested', {
                bubbles: true
            }));
        });

        // Download button
        const downloadBtn = this.querySelector('#btn-download-output');
        downloadBtn?.addEventListener('click', () => {
            this.dispatchEvent(new CustomEvent('download-requested', {
                bubbles: true
            }));
        });

        // Mode change listener (for future preview mode)
        this.addEventListener('mode-selected', (e) => {
            if (e.detail.columnId === 'created') {
                this.switchMode(e.detail.mode);
            }
        });
    }

    switchMode(mode) {
        console.log(`✨ ColumnCreated: Switching to ${mode} mode`);
        this.mode = mode;
        
        const column = this.querySelector('#column-created');
        column.setAttribute('data-mode', mode);
    }

    renderOutput() {
        const output = this.querySelector('#created-html-output');
        
        if (!this.createdHtml.trim()) {
            output.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">✨</div>
                    <div class="empty-state-text">Rebuilt HTML will appear here after reconstruction</div>
                </div>
            `;
            return;
        }

        const highlighted = Syntax__Highlighter.highlight(this.createdHtml, 'html');
        output.innerHTML = `<pre class="syntax-output">${highlighted}</pre>`;
        console.log('✨ ColumnCreated: Output rendered');
    }

    // Public API
    setHtml(html) {
        //console.log('✨ ColumnCreated: Setting HTML', html?.substring(0, 100));
        this.createdHtml = html;
        this.renderOutput();
    }

    getHtml() {
        return this.createdHtml;
    }

    clear() {
        this.createdHtml = '';
        this.renderOutput();
    }
}

customElements.define('column-created', ColumnCreated);
console.log('✅ ColumnCreated component registered');
